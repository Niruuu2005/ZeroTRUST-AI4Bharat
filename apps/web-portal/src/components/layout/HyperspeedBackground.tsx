"use client";

import { usePathname } from 'next/navigation';
import Hyperspeed, { hyperspeedPresets } from '@/components/ui/Hyperspeed';

// Routes that show the Hyperspeed background
const HYPERSPEED_ROUTES = ['/', '/extension'];

export default function HyperspeedBackground() {
    const pathname = usePathname();
    const visible = HYPERSPEED_ROUTES.includes(pathname);

    // Always mounted — never unmounts between navigations.
    // We only toggle CSS opacity so the WebGL context stays alive.
    return (
        <div
            className="fixed inset-0 z-0 pointer-events-none"
            style={{
                opacity: visible ? 1 : 0,
                transition: 'opacity 0.5s ease',
            }}
        >
            <Hyperspeed effectOptions={hyperspeedPresets.one} />
        </div>
    );
}
