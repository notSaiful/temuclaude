import nodemailer from 'nodemailer';

/**
 * TemuClaude Email System
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

function getEmailProvider() {
  const configuredProvider = (process.env.EMAIL_PROVIDER || '').toLowerCase();
  if (configuredProvider) return configuredProvider;
  if (process.env.HOSTINGER_EMAIL_PASSWORD || process.env.SMTP_PASSWORD) return 'hostinger';
  return 'resend';
}

const RESEND_API_URL = 'https://api.resend.com/emails';

// Email addresses for TemuClaude
// Note: temuclaude.com is the verified sending domain in Resend.
// Hostinger DNS must have SPF TXT on root domain pointing to amazonses.com.
export const EMAIL_ADDRESSES = {
  hello: 'TemuClaude <hello@temuclaude.com>',
  support: 'TemuClaude Support <support@temuclaude.com>',
  legal: 'TemuClaude Legal <legal@temuclaude.com>',
  security: 'TemuClaude Security <security@temuclaude.com>',
  api: 'TemuClaude API <api@temuclaude.com>',
  billing: 'TemuClaude Billing <billing@temuclaude.com>',
  marketing: 'TemuClaude <marketing@temuclaude.com>',
  saiful: 'TemuClaude <saiful@temuclaude.com>',
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

function escapeHtml(value: string) {
  return value.replace(/[&<>"']/g, (char) => {
    switch (char) {
      case '&': return '&amp;';
      case '<': return '&lt;';
      case '>': return '&gt;';
      case '"': return '&quot;';
      case '\'': return '&#39;';
      default: return char;
    }
  });
}

function emailText(value: string) {
  return value.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
}

function logField(value: unknown) {
  return String(value ?? '').replace(/[\r\n]/g, ' ').slice(0, 500);
}

function getResendApiKey() {
  return process.env.RESEND_API_KEY || '';
}

function getDefaultFromAddress() {
  return process.env.EMAIL_FROM || process.env.RESEND_FROM_EMAIL || EMAIL_ADDRESSES.hello;
}

function extractEmailAddress(value: string) {
  const match = value.match(/<([^>]+)>/);
  return (match?.[1] || value).trim();
}

function getSmtpConfig() {
  const user = process.env.SMTP_USER || process.env.HOSTINGER_EMAIL_USER || 'hello@temuclaude.com';

  return {
    host: process.env.SMTP_HOST || process.env.HOSTINGER_SMTP_HOST || 'smtp.hostinger.com',
    port: Number(process.env.SMTP_PORT || process.env.HOSTINGER_SMTP_PORT || 465),
    secure: (process.env.SMTP_SECURE || process.env.HOSTINGER_SMTP_SECURE || 'true') !== 'false',
    user: extractEmailAddress(user),
    pass: process.env.SMTP_PASSWORD || process.env.HOSTINGER_EMAIL_PASSWORD || '',
  };
}

function isSmtpProvider() {
  const provider = getEmailProvider();
  return provider === 'smtp' || provider === 'hostinger';
}

export function getEmailDeliveryStatus() {
  const provider = getEmailProvider();
  const smtp = getSmtpConfig();
  const resendConfigured = Boolean(getResendApiKey());
  const smtpConfigured = Boolean(smtp.user && smtp.pass);

  return {
    provider,
    from: getDefaultFromAddress(),
    resendConfigured,
    smtpConfigured,
    ready: isSmtpProvider() ? smtpConfigured : provider === 'resend' && resendConfigured,
  };
}

async function sendEmailViaSmtp(params: {
  to: string[];
  from: string;
  subject: string;
  html: string;
  replyTo?: string;
}): Promise<EmailResult> {
  const smtp = getSmtpConfig();
  if (!smtp.pass) {
    console.error('[EMAIL] SMTP password not configured');
    return { success: false, error: 'SMTP password not configured' };
  }

  const transporter = nodemailer.createTransport({
    host: smtp.host,
    port: smtp.port,
    secure: smtp.secure,
    auth: {
      user: smtp.user,
      pass: smtp.pass,
    },
  });

  const result = await transporter.sendMail({
    from: params.from,
    to: params.to.join(', '),
    subject: params.subject,
    // SMTP is the compatibility fallback. Plain text prevents a caller from
    // turning user-provided content into executable email markup.
    text: emailText(params.html),
    replyTo: params.replyTo,
  });

  return { success: true, id: result.messageId };
}

/**
 * Send an email via the configured production provider.
 */
export async function sendEmail({
  to,
  from,
  subject,
  html,
  replyTo,
  type = 'notification',
  tags = [],
}: SendEmailParams): Promise<EmailResult> {
  const recipients = Array.isArray(to) ? to : [to];
  const sender = from || getDefaultFromAddress();

  // Validate from address — accept root domain and any subdomain (e.g. send.temuclaude.com)
  const fromEmail = extractEmailAddress(sender);
  if (!fromEmail.endsWith('@temuclaude.com') && !fromEmail.endsWith('.temuclaude.com') && !sender.includes('@resend.dev')) {
    console.error('[EMAIL] From address must use temuclaude.com domain');
    return { success: false, error: 'Invalid from address' };
  }

  try {
    if (isSmtpProvider()) {
      const result = await sendEmailViaSmtp({ to: recipients, from: sender, subject, html, replyTo });
      console.log(`[EMAIL] Sent via SMTP (${logField(type)}): ${logField(subject)} -> ${recipients.map(logField).join(', ')}`);
      return result;
    }

    const resendApiKey = getResendApiKey();
    if (!resendApiKey) {
      console.error('[EMAIL] RESEND_API_KEY not set');
      return { success: false, error: 'RESEND_API_KEY not configured' };
    }

    const uniqueTags = Array.from(new Set(tags));
    const body: Record<string, unknown> = {
      from: sender,
      to: recipients,
      subject,
      html,
      tags: [
        { name: 'type', value: type },
        { name: 'source', value: 'hasan' },
        ...uniqueTags.map((t, idx) => ({ name: `tag_${idx + 1}`, value: t })),
      ],
    };

    if (replyTo) {
      body.reply_to = replyTo;
    }

    const response = await fetch(RESEND_API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${resendApiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(15_000),
    });

    const data = await response.json().catch(() => ({})) as { id?: string; message?: string; name?: string };

    if (!response.ok) {
      console.error('[EMAIL] Resend request failed:', response.status, logField(data.name || data.message || 'Unknown error'));
      return { success: false, error: data.message || data.name || `Resend request failed (${response.status})` };
    }

    console.log(`[EMAIL] Sent (${logField(type)}): ${logField(subject)} → ${recipients.map(logField).join(', ')} [${logField(data.id)}]`);
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
          · 20 queries/day after sign-in<br>
          · 50K monthly credits<br>
          · Full 10-layer orchestration<br>
          · All 8 models<br>
          · Visible orchestration panel
        </p>
        <p style="color: #475569; line-height: 1.6; font-size: 14px;">
          <strong>Need more?</strong> Developer starts at $19/mo for 5M monthly credits + API access.
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
 * Send one-time password for sign in and account creation.
 */
export async function sendOtpEmail(
  userEmail: string,
  code: string,
  purpose: 'signin' | 'signup' = 'signin',
): Promise<EmailResult> {
  const purposeLabel = purpose === 'signup' ? 'create your TemuClaude account' : 'sign in to TemuClaude';
  const safeCode = escapeHtml(code);
  const html = `
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 560px; margin: 0 auto; padding: 24px;">
      <div style="background: #111827; padding: 28px; border-radius: 12px 12px 0 0;">
        <h1 style="color: #ffffff; margin: 0; font-size: 24px;">TemuClaude verification code</h1>
        <p style="color: #cbd5e1; margin: 8px 0 0 0;">Use this code to ${purposeLabel}.</p>
      </div>
      <div style="background: #f8fafc; padding: 28px; border: 1px solid #e2e8f0; border-radius: 0 0 12px 12px;">
        <p style="color: #334155; margin: 0 0 18px 0;">Your 6-digit code is:</p>
        <div style="font-size: 32px; letter-spacing: 8px; font-weight: 700; color: #0f172a; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px 20px; text-align: center;">
          ${safeCode}
        </div>
        <p style="color: #64748b; font-size: 13px; line-height: 1.6; margin: 18px 0 0 0;">
          This code expires in 10 minutes. If you did not request it, you can safely ignore this email.
        </p>
      </div>
    </div>
  `;

  return sendEmail({
    to: userEmail,
    from: EMAIL_ADDRESSES.hello,
    subject: `${safeCode} is your TemuClaude verification code`,
    html,
    type: 'security',
    tags: ['otp', purpose],
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
