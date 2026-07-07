/**
 * TemuClaude Email System — Resend Integration
 * 
 * Handles all automated email communication:
 * - Customer support
 * - User feedback
 * - Legal notices
 * - API communications
 * - Email marketing
 * - Welcome / onboarding
 * - Billing / receipts
 * - Security alerts
 * 
 * Managed by Hasan autonomous system.
 */

const RESEND_API_KEY = process.env.RESEND_API_KEY || '';
const RESEND_API_URL = 'https://api.resend.com/emails';

// Email addresses for TemuClaude
export const EMAIL_ADDRESSES = {
  hello: 'hello@temuclaude.com',
  support: 'support@temuclaude.com',
  legal: 'legal@temuclaude.com',
  security: 'security@temuclaude.com',
  api: 'api@temuclaude.com',
  billing: 'billing@temuclaude.com',
  marketing: 'marketing@temuclaude.com',
  saiful: 'saiful@temuclaude.com',
} as const;

export type EmailType =
  | 'support'
  | 'feedback'
  | 'legal'
  | 'api'
  | 'marketing'
  | 'welcome'
  | 'billing'
  | 'security'
  | 'notification';

interface SendEmailParams {
  to: string | string[];
  from?: string;
  subject: string;
  html: string;
  replyTo?: string;
  type?: EmailType;
  tags?: string[];
}

interface EmailResult {
  success: boolean;
  id?: string;
  error?: string;
}

/**
 * Send an email via Resend API
 */
export async function sendEmail({
  to,
  from = EMAIL_ADDRESSES.hello,
  subject,
  html,
  replyTo,
  type = 'notification',
  tags = [],
}: SendEmailParams): Promise<EmailResult> {
  if (!RESEND_API_KEY) {
    console.error('[EMAIL] RESEND_API_KEY not set');
    return { success: false, error: 'RESEND_API_KEY not configured' };
  }

  const recipients = Array.isArray(to) ? to : [to];

  // Validate from address
  if (!from.includes('@temuclaude.com') && !from.includes('@resend.dev')) {
    console.error('[EMAIL] From address must use temuclaude.com domain');
    return { success: false, error: 'Invalid from address' };
  }

  try {
    const body: Record<string, unknown> = {
      from,
      to: recipients,
      subject,
      html,
      tags: [
        { name: 'type', value: type },
        { name: 'source', value: 'hasan' },
        ...tags.map(t => ({ name: 'tag', value: t })),
      ],
    };

    if (replyTo) {
      body.reply_to = replyTo;
    }

    const response = await fetch(RESEND_API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error('[EMAIL] Send failed:', data);
      return { success: false, error: data.message || 'Unknown error' };
    }

    console.log(`[EMAIL] Sent (${type}): ${subject} → ${recipients.join(', ')} [${data.id}]`);
    return { success: true, id: data.id };
  } catch (error) {
    console.error('[EMAIL] Error:', error);
    return { success: false, error: String(error) };
  }
}

/**
 * Send customer support email
 */
export async function sendSupportEmail(
  userEmail: string,
  userName: string,
  message: string,
  category: string = 'general',
): Promise<EmailResult> {
  const html = `
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="background: linear-gradient(135deg, #0f172a, #1e293b); padding: 30px; border-radius: 12px 12px 0 0;">
        <h1 style="color: #f8fafc; margin: 0; font-size: 24px; font-weight: 600;">TemuClaude Support</h1>
        <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 14px;">New support request received</p>
      </div>
      <div style="background: #f8fafc; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #e2e8f0;">
        <table style="width: 100%; border-collapse: collapse;">
          <tr><td style="padding: 8px 0; color: #64748b; font-size: 14px; width: 100px;">From:</td><td style="padding: 8px 0; color: #0f172a; font-weight: 500;">${userName} &lt;${userEmail}&gt;</td></tr>
          <tr><td style="padding: 8px 0; color: #64748b; font-size: 14px;">Category:</td><td style="padding: 8px 0; color: #0f172a;">${category}</td></tr>
          <tr><td style="padding: 8px 0; color: #64748b; font-size: 14px; vertical-align: top;">Message:</td><td style="padding: 8px 0; color: #0f172a; white-space: pre-wrap;">${message}</td></tr>
        </table>
        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
          <p style="color: #64748b; font-size: 13px; margin: 0;">Reply directly to this email to respond to the customer.</p>
        </div>
      </div>
      <div style="text-align: center; padding: 20px; color: #94a3b8; font-size: 12px;">
        TemuClaude · Multi-Model AI Orchestration · temuclaude.com
      </div>
    </div>
  `;

  return sendEmail({
    to: EMAIL_ADDRESSES.support,
    from: EMAIL_ADDRESSES.hello,
    replyTo: userEmail,
    subject: `[Support] ${category} — ${userName}`,
    html,
    type: 'support',
    tags: [category],
  });
}

/**
 * Send user feedback email
 */
export async function sendFeedbackEmail(
  userEmail: string,
  userName: string,
  rating: number,
  feedback: string,
): Promise<EmailResult> {
  const stars = '★'.repeat(rating) + '☆'.repeat(5 - rating);
  const html = `
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="background: linear-gradient(135deg, #0f172a, #1e293b); padding: 30px; border-radius: 12px 12px 0 0;">
        <h1 style="color: #f8fafc; margin: 0; font-size: 24px;">User Feedback</h1>
        <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 14px;">Rating: ${stars} (${rating}/5)</p>
      </div>
      <div style="background: #f8fafc; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #e2e8f0;">
        <p style="color: #64748b; font-size: 14px; margin: 0 0 5px 0;">From: ${userName} &lt;${userEmail}&gt;</p>
        <p style="color: #0f172a; white-space: pre-wrap; margin: 15px 0;">${feedback}</p>
      </div>
    </div>
  `;

  return sendEmail({
    to: EMAIL_ADDRESSES.hello,
    from: EMAIL_ADDRESSES.hello,
    replyTo: userEmail,
    subject: `[Feedback] ${rating}/5 — ${userName}`,
    html,
    type: 'feedback',
    tags: [rating >= 4 ? 'positive' : 'negative'],
  });
}

/**
 * Send legal notice email
 */
export async function sendLegalNotice(
  to: string,
  subject: string,
  content: string,
): Promise<EmailResult> {
  const html = `
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 30px; border-radius: 12px 12px 0 0;">
        <h1 style="color: #f8fafc; margin: 0; font-size: 22px;">TemuClaude Legal Notice</h1>
        <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 13px;">This is an official communication from TemuClaude.</p>
      </div>
      <div style="background: #f8fafc; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #e2e8f0;">
        <p style="color: #0f172a; white-space: pre-wrap; line-height: 1.6;">${content}</p>
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
          <p style="color: #64748b; font-size: 13px;">Mohammad Saiful Haque</p>
          <p style="color: #64748b; font-size: 13px;">TemuClaude · temuclaude.com</p>
          <p style="color: #64748b; font-size: 13px;">Legal contact: legal@temuclaude.com</p>
        </div>
      </div>
    </div>
  `;

  return sendEmail({
    to,
    from: EMAIL_ADDRESSES.legal,
    subject: `[Legal] ${subject}`,
    html,
    type: 'legal',
    tags: ['legal-notice'],
  });
}

/**
 * Send API communication email (key generation, usage alerts, etc)
 */
export async function sendApiEmail(
  to: string,
  subject: string,
  content: string,
  action: string = 'notification',
): Promise<EmailResult> {
  const html = `
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="background: linear-gradient(135deg, #0f172a, #1e293b); padding: 30px; border-radius: 12px 12px 0 0;">
        <h1 style="color: #f8fafc; margin: 0; font-size: 22px;">TemuClaude API</h1>
        <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 13px;">${action}</p>
      </div>
      <div style="background: #f8fafc; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #e2e8f0;">
        <p style="color: #0f172a; white-space: pre-wrap; line-height: 1.6;">${content}</p>
        <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #e2e8f0;">
          <p style="color: #64748b; font-size: 13px;">API documentation: https://temuclaude.com/docs</p>
          <p style="color: #64748b; font-size: 13px;">API support: api@temuclaude.com</p>
        </div>
      </div>
    </div>
  `;

  return sendEmail({
    to,
    from: EMAIL_ADDRESSES.api,
    subject: `[API] ${subject}`,
    html,
    type: 'api',
    tags: [action],
  });
}

/**
 * Send marketing email (newsletter, announcements)
 */
export async function sendMarketingEmail(
  to: string | string[],
  subject: string,
  content: string,
  unsubscribeUrl?: string,
): Promise<EmailResult> {
  const unsub = unsubscribeUrl || 'https://temuclaude.com/unsubscribe';
  const html = `
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="background: linear-gradient(135deg, #0f172a, #1e293b); padding: 30px; border-radius: 12px 12px 0 0;">
        <h1 style="color: #f8fafc; margin: 0; font-size: 24px;">TemuClaude</h1>
        <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 14px;">Multi-Model AI Orchestration</p>
      </div>
      <div style="background: #f8fafc; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #e2e8f0;">
        ${content}
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
          <p style="color: #64748b; font-size: 13px; margin: 0;">
            You're receiving this because you subscribed at temuclaude.com.<br>
            <a href="${unsub}" style="color: #3b82f6;">Unsubscribe</a> · 
            <a href="https://temuclaude.com/privacy" style="color: #3b82f6;">Privacy Policy</a>
          </p>
        </div>
      </div>
      <div style="text-align: center; padding: 20px; color: #94a3b8; font-size: 12px;">
        TemuClaude · MIT Licensed · 25% of profit to charity
      </div>
    </div>
  `;

  return sendEmail({
    to,
    from: EMAIL_ADDRESSES.marketing,
    subject,
    html,
    type: 'marketing',
    tags: ['newsletter'],
  });
}

/**
 * Send welcome email to new users
 */
export async function sendWelcomeEmail(
  userEmail: string,
  userName?: string,
): Promise<EmailResult> {
  const name = userName || 'there';
  const html = `
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="background: linear-gradient(135deg, #0f172a, #1e293b); padding: 40px 30px; border-radius: 12px 12px 0 0; text-align: center;">
        <h1 style="color: #f8fafc; margin: 0; font-size: 28px;">Welcome to TemuClaude</h1>
        <p style="color: #94a3b8; margin: 10px 0 0 0; font-size: 15px;">One question. Eight minds. One superior answer.</p>
      </div>
      <div style="background: #f8fafc; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #e2e8f0;">
        <p style="color: #0f172a; font-size: 16px;">Hi ${name},</p>
        <p style="color: #475569; line-height: 1.6;">
          You now have access to 8 AI models working together behind one API.
          Every question you ask gets routed, fused, verified, and quality-checked — 
          automatically. You never pick models. TemuClaude does it for you.
        </p>
        <div style="margin: 25px 0;">
          <a href="https://temuclaude.com/playground" style="background: #3b82f6; color: white; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block;">Try the Playground</a>
        </div>
        <p style="color: #475569; line-height: 1.6; font-size: 14px;">
          <strong>What you get (free):</strong><br>
          · 20 queries/day — no signup required<br>
          · Full 10-layer orchestration<br>
          · All 8 models<br>
          · Visible orchestration panel
        </p>
        <p style="color: #475569; line-height: 1.6; font-size: 14px;">
          <strong>Need more?</strong> Developer plan starts at $15/mo for 50,000 queries + API access.
        </p>
        <div style="margin-top: 25px; padding-top: 15px; border-top: 1px solid #e2e8f0;">
          <p style="color: #64748b; font-size: 13px; margin: 0;">
            Questions? Reply to this email or visit our 
            <a href="https://temuclaude.com/docs" style="color: #3b82f6;">documentation</a>.
          </p>
        </div>
      </div>
      <div style="text-align: center; padding: 20px; color: #94a3b8; font-size: 12px;">
        TemuClaude · MIT Licensed · 25% of profit to charity<br>
        <a href="https://temuclaude.com" style="color: #94a3b8;">temuclaude.com</a>
      </div>
    </div>
  `;

  return sendEmail({
    to: userEmail,
    from: EMAIL_ADDRESSES.hello,
    subject: `Welcome to TemuClaude, ${name}!`,
    html,
    type: 'welcome',
    tags: ['onboarding'],
  });
}

/**
 * Send billing/receipt email
 */
export async function sendBillingEmail(
  to: string,
  subject: string,
  amount: string,
  plan: string,
  period: string,
  receiptId: string,
): Promise<EmailResult> {
  const html = `
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="background: linear-gradient(135deg, #0f172a, #1e293b); padding: 30px; border-radius: 12px 12px 0 0;">
        <h1 style="color: #f8fafc; margin: 0; font-size: 22px;">TemuClaude Receipt</h1>
        <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 14px;">Receipt #${receiptId}</p>
      </div>
      <div style="background: #f8fafc; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #e2e8f0;">
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
          <tr><td style="padding: 10px 0; color: #64748b; font-size: 14px;">Plan:</td><td style="padding: 10px 0; color: #0f172a; font-weight: 600; text-align: right;">${plan}</td></tr>
          <tr><td style="padding: 10px 0; color: #64748b; font-size: 14px;">Billing period:</td><td style="padding: 10px 0; color: #0f172a; text-align: right;">${period}</td></tr>
          <tr><td style="padding: 10px 0; color: #64748b; font-size: 14px;">Amount:</td><td style="padding: 10px 0; color: #0f172a; font-weight: 700; font-size: 18px; text-align: right;">${amount}</td></tr>
        </table>
        <div style="padding-top: 15px; border-top: 2px solid #e2e8f0;">
          <p style="color: #64748b; font-size: 13px; margin: 0;">
            25% of profit from this payment goes to charity — food relief, community kitchens, medical clinics, and education programs.
          </p>
        </div>
        <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #e2e8f0;">
          <p style="color: #64748b; font-size: 13px; margin: 0;">
            Billing questions? Contact billing@temuclaude.com<br>
            Manage your subscription: <a href="https://temuclaude.com/pricing" style="color: #3b82f6;">temuclaude.com/pricing</a>
          </p>
        </div>
      </div>
    </div>
  `;

  return sendEmail({
    to,
    from: EMAIL_ADDRESSES.billing,
    subject: `Receipt — ${plan} — ${amount}`,
    html,
    type: 'billing',
    tags: ['receipt', plan.toLowerCase()],
  });
}

/**
 * Send security alert email
 */
export async function sendSecurityAlert(
  to: string,
  alertType: string,
  message: string,
): Promise<EmailResult> {
  const html = `
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="background: linear-gradient(135deg, #7f1d1d, #991b1b); padding: 30px; border-radius: 12px 12px 0 0;">
        <h1 style="color: #fef2f2; margin: 0; font-size: 22px;">Security Alert</h1>
        <p style="color: #fecaca; margin: 5px 0 0 0; font-size: 14px;">${alertType}</p>
      </div>
      <div style="background: #fef2f2; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #fecaca;">
        <p style="color: #7f1d1d; white-space: pre-wrap; line-height: 1.6;">${message}</p>
        <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #fecaca;">
          <p style="color: #991b1b; font-size: 13px; margin: 0; font-weight: 600;">
            If this was not you, contact security@temuclaude.com immediately.
          </p>
        </div>
      </div>
    </div>
  `;

  return sendEmail({
    to,
    from: EMAIL_ADDRESSES.security,
    subject: `[Security] ${alertType}`,
    html,
    type: 'security',
    tags: ['security-alert', alertType.toLowerCase()],
  });
}

/**
 * Batch send (for marketing campaigns)
 */
export async function sendBatch(
  recipients: string[],
  subject: string,
  content: string,
  type: EmailType = 'marketing',
): Promise<{ sent: number; failed: number; errors: string[] }> {
  let sent = 0;
  let failed = 0;
  const errors: string[] = [];

  // Send in batches of 50 to avoid rate limits
  const batchSize = 50;
  for (let i = 0; i < recipients.length; i += batchSize) {
    const batch = recipients.slice(i, i + batchSize);
    const promises = batch.map(async (email) => {
      const result = type === 'marketing'
        ? await sendMarketingEmail(email, subject, content)
        : await sendEmail({ to: email, subject, html: content, type });
      if (result.success) {
        sent++;
      } else {
        failed++;
        errors.push(`${email}: ${result.error}`);
      }
    });
    await Promise.all(promises);
    // Rate limit: 100ms between batches
    if (i + batchSize < recipients.length) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }

  console.log(`[EMAIL] Batch complete: ${sent} sent, ${failed} failed`);
  return { sent, failed, errors };
}