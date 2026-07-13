import { redirect } from 'next/navigation';

/** Keep public sign-up links stable while using the shared auth screen. */
export default function SignupPage() {
  redirect('/login?mode=signup');
}
