import { NextResponse } from 'next/server';
import { isHostingerApiConfigured } from '@/lib/hostinger';
import { getEmailDeliveryStatus } from '@/lib/email';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET() {
  const status = getEmailDeliveryStatus();
  const imapConfigured = Boolean(
    process.env.HOSTINGER_IMAP_HOST &&
    process.env.HOSTINGER_IMAP_PORT &&
    (process.env.SMTP_USER || process.env.HOSTINGER_EMAIL_USER)
  );

  return NextResponse.json({
    ...status,
    smtpHost: process.env.SMTP_HOST || process.env.HOSTINGER_SMTP_HOST || 'smtp.hostinger.com',
    smtpPort: Number(process.env.SMTP_PORT || process.env.HOSTINGER_SMTP_PORT || 465),
    imapHost: process.env.HOSTINGER_IMAP_HOST || 'imap.hostinger.com',
    imapPort: Number(process.env.HOSTINGER_IMAP_PORT || 993),
    imapConfigured,
    hostingerApiConfigured: isHostingerApiConfigured(),
    inboundWebhookConfigured: Boolean(process.env.INBOUND_EMAIL_WEBHOOK_SECRET),
  });
}
