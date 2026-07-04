'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Navbar } from '@/components/Navbar';

function PaymentSuccessContent() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const subscriptionId = searchParams.get('subscription_id');
    const paymentId = searchParams.get('payment_id');
    const orderId = searchParams.get('order_id');
    const plan = searchParams.get('plan');

    if (!subscriptionId && !paymentId) {
      setStatus('success');
      setMessage('Your subscription is now active. Check your email for details.');
      return;
    }

    const verify = async () => {
      try {
        const res = await fetch('/api/payments/verify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            razorpayOrderId: orderId,
            razorpayPaymentId: paymentId,
            razorpaySignature: searchParams.get('signature'),
            subscriptionId,
            planId: plan,
          }),
        });
        const data = await res.json();

        if (res.ok && data.verified) {
          setStatus('success');
          setMessage(`Payment verified! Your ${plan || 'Pro'} plan is now active.`);
        } else {
          setStatus('error');
          setMessage(data.error || 'Payment verification failed. Please contact support.');
        }
      } catch (err: any) {
        setStatus('error');
        setMessage(err.message || 'Something went wrong.');
      }
    };

    verify();
  }, [searchParams]);

  return (
    <>
      {status === 'verifying' && (
        <>
          <div className="w-16 h-16 mx-auto mb-6 border-4 border-accent-primary border-t-transparent rounded-full animate-spin" />
          <h1 className="text-2xl font-light text-text-primary mb-2" style={{ fontWeight: 300 }}>
            Verifying your payment...
          </h1>
          <p className="text-text-secondary">Please wait while we confirm your subscription.</p>
        </>
      )}

      {status === 'success' && (
        <>
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-green-100 flex items-center justify-center">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#788C5D" strokeWidth="3">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <h1 className="text-2xl font-light text-text-primary mb-2" style={{ fontWeight: 300 }}>
            Welcome to Temuclaude!
          </h1>
          <p className="text-text-secondary mb-8">{message}</p>
          <div className="space-y-3">
            <a href="/playground" className="btn-accent inline-block w-full">Go to Playground</a>
            <a href="/docs" className="btn-secondary inline-block w-full">Read the Docs</a>
          </div>
        </>
      )}

      {status === 'error' && (
        <>
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-red-100 flex items-center justify-center">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#dc2626" strokeWidth="3">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </div>
          <h1 className="text-2xl font-light text-text-primary mb-2" style={{ fontWeight: 300 }}>
            Verification Issue
          </h1>
          <p className="text-text-secondary mb-8">{message}</p>
          <a href="/pricing" className="btn-secondary inline-block">Back to Pricing</a>
        </>
      )}
    </>
  );
}

export default function PaymentSuccessPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6 min-h-screen flex items-center">
        <div className="container-max max-w-md mx-auto text-center">
          <Suspense fallback={
            <>
              <div className="w-16 h-16 mx-auto mb-6 border-4 border-accent-primary border-t-transparent rounded-full animate-spin" />
              <h1 className="text-2xl font-light text-text-primary mb-2" style={{ fontWeight: 300 }}>
                Loading...
              </h1>
            </>
          }>
            <PaymentSuccessContent />
          </Suspense>
        </div>
      </main>
    </>
  );
}