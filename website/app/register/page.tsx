import { redirect } from 'next/navigation';

/** Legacy registration links resolve to the supported sign-up route. */
export default function RegisterPage() {
  redirect('/signup');
}
