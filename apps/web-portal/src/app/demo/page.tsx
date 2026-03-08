"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

// Redirects to the home verify form with a pre-filled demo claim
export default function DemoPage() {
    const router = useRouter();
    useEffect(() => {
        router.replace(
            '/verify?q=The+James+Webb+Space+Telescope+has+detected+signs+of+biological+activity+on+an+exoplanet&mode=text&source=web'
        );
    }, [router]);
    return null;
}
