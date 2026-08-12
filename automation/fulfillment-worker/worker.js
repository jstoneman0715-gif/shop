/**
 * All The Rage — automated digital fulfilment.
 *
 * A single Cloudflare Worker that closes the loop between "customer paid" and
 * "customer has the file", with nothing for you to do by hand:
 *
 *   Stripe  --(checkout.session.completed webhook)-->  POST /stripe-webhook
 *        verify signature -> map line items to products -> mint signed links
 *        -> email the customer
 *
 *   Customer clicks a link              -->  GET /download?p=&exp=&sig=
 *        verify HMAC + expiry -> stream the file straight out of your R2 bucket
 *
 * Everything it touches is yours: your Stripe account, your R2 bucket, your
 * domain. No storefront platform sits in the middle and no one takes a cut
 * beyond Stripe's card fee.
 *
 * Deploy: see automation/fulfillment-worker/README.md
 */

const DEFAULT_TTL_SECONDS = 60 * 60 * 24 * 14; // links stay good for two weeks

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === "/stripe-webhook" && request.method === "POST") {
      return handleWebhook(request, env, ctx);
    }
    if (url.pathname === "/download" && request.method === "GET") {
      return handleDownload(url, env);
    }
    if (url.pathname === "/health") {
      return json({ ok: true, service: "shop-fulfilment" });
    }
    return new Response("Not found", { status: 404 });
  },
};

/* ------------------------------------------------------------------ webhook */

async function handleWebhook(request, env, ctx) {
  const signature = request.headers.get("stripe-signature") || "";
  const payload = await request.text();

  const verified = await verifyStripeSignature(payload, signature, env.STRIPE_WEBHOOK_SECRET);
  if (!verified) {
    // Never trust an unverified body: anyone can POST to a public URL.
    return new Response("Invalid signature", { status: 400 });
  }

  const event = JSON.parse(payload);
  if (event.type !== "checkout.session.completed") {
    return json({ received: true, ignored: event.type });
  }

  const session = event.data.object;
  if (session.payment_status !== "paid") {
    return json({ received: true, ignored: "unpaid session" });
  }

  // Deliver in the background so Stripe always gets a fast 200 and does not retry.
  ctx.waitUntil(deliver(session, env));
  return json({ received: true });
}

async function deliver(session, env) {
  const email = session.customer_details?.email || session.customer_email;
  if (!email) {
    console.error("checkout session has no email", session.id);
    return;
  }

  const slugs = await slugsForSession(session, env);
  if (slugs.length === 0) {
    console.log("no digital products on session", session.id);
    return;
  }

  const expiry = Math.floor(Date.now() / 1000) + Number(env.LINK_TTL_SECONDS || DEFAULT_TTL_SECONDS);
  const links = [];
  for (const slug of slugs) {
    const signature = await sign(`${slug}:${expiry}`, env.DOWNLOAD_SIGNING_SECRET);
    const href = `${env.PUBLIC_WORKER_URL.replace(/\/$/, "")}/download?p=${encodeURIComponent(
      slug
    )}&exp=${expiry}&sig=${signature}`;
    links.push({ slug, href });
  }

  await sendEmail(email, links, session, env);
}

/**
 * Work out which digital products were bought.
 *
 * Preferred route: set `metadata.slug` on each Stripe Price or Product so the
 * mapping lives in Stripe and never drifts. Falls back to the lookup_key, then
 * to SLUG_BY_PRICE (a JSON map in the worker's env) for prices created before
 * metadata was added.
 */
async function slugsForSession(session, env) {
  const response = await fetch(
    `https://api.stripe.com/v1/checkout/sessions/${session.id}/line_items?limit=100&expand[]=data.price.product`,
    { headers: { Authorization: `Bearer ${env.STRIPE_SECRET_KEY}` } }
  );
  if (!response.ok) {
    console.error("stripe line_items failed", response.status, await response.text());
    return [];
  }

  const overrides = safeJson(env.SLUG_BY_PRICE) || {};
  const { data = [] } = await response.json();
  const slugs = new Set();

  for (const item of data) {
    const price = item.price || {};
    const product = price.product || {};
    const slug =
      price.metadata?.slug ||
      product.metadata?.slug ||
      price.lookup_key ||
      overrides[price.id];
    if (slug) slugs.add(slug);
  }
  return [...slugs];
}

/* ----------------------------------------------------------------- download */

async function handleDownload(url, env) {
  const slug = url.searchParams.get("p") || "";
  const expiry = Number(url.searchParams.get("exp") || 0);
  const signature = url.searchParams.get("sig") || "";

  if (!slug || !expiry || !signature) {
    return new Response("Missing link parameters", { status: 400 });
  }
  if (Math.floor(Date.now() / 1000) > expiry) {
    return new Response(
      "This download link has expired. Email support and a fresh one will be sent.",
      { status: 410 }
    );
  }

  const expected = await sign(`${slug}:${expiry}`, env.DOWNLOAD_SIGNING_SECRET);
  if (!timingSafeEqual(expected, signature)) {
    return new Response("Invalid link", { status: 403 });
  }

  const key = `${slug}.zip`;
  const object = await env.PRODUCTS.get(key);
  if (!object) {
    console.error("missing R2 object", key);
    return new Response("File not found — email support and it will be sent by hand.", {
      status: 404,
    });
  }

  return new Response(object.body, {
    headers: {
      "Content-Type": object.httpMetadata?.contentType || "application/zip",
      "Content-Disposition": `attachment; filename="${slug}.zip"`,
      "Cache-Control": "private, no-store",
    },
  });
}

/* -------------------------------------------------------------------- email */

async function sendEmail(to, links, session, env) {
  const list = links
    .map((l) => `<li><a href="${escapeHtml(l.href)}">${escapeHtml(prettify(l.slug))}</a></li>`)
    .join("");

  const html = `
    <div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;color:#111;line-height:1.6">
      <h2 style="color:#ff6b35;margin-bottom:.2rem">All The Rage</h2>
      <p>Thanks for your order — here is everything you bought.</p>
      <ul>${list}</ul>
      <p style="font-size:.9em;color:#555">
        These links work for the next two weeks and are tied to your order.
        If one expires or fails, reply to this email and a fresh link will be sent.
      </p>
      <p style="font-size:.85em;color:#777">Order reference: ${escapeHtml(session.id)}</p>
    </div>`;

  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: env.FROM_EMAIL,
      to: [to],
      subject: "Your All The Rage download links",
      html,
    }),
  });

  if (!response.ok) {
    // Logged, not thrown: the customer still has the confirmation page, and
    // Stripe should not be told the webhook failed for an email provider blip.
    console.error("email send failed", response.status, await response.text());
  }
}

/* -------------------------------------------------------------------- crypto */

async function verifyStripeSignature(payload, header, secret) {
  if (!header || !secret) return false;

  const parts = Object.fromEntries(
    header.split(",").map((piece) => piece.split("=").map((s) => s.trim()))
  );
  const timestamp = parts.t;
  const provided = parts.v1;
  if (!timestamp || !provided) return false;

  // Reject replays of an old, previously valid payload.
  const age = Math.abs(Math.floor(Date.now() / 1000) - Number(timestamp));
  if (!Number.isFinite(age) || age > 300) return false;

  const expected = await sign(`${timestamp}.${payload}`, secret);
  return timingSafeEqual(expected, provided);
}

async function sign(message, secret) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const mac = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(message));
  return [...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function timingSafeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

/* --------------------------------------------------------------------- util */

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function safeJson(value) {
  try {
    return value ? JSON.parse(value) : null;
  } catch {
    return null;
  }
}

function prettify(slug) {
  return slug.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[c]);
}
