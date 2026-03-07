"use client";

import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { Home, BrainCircuit, PuzzleIcon, Info } from 'lucide-react';

const NAV_LINKS = [
    { name: 'Home',       href: '/',          icon: Home          },
    { name: 'Agents',     href: '/#agents',   icon: BrainCircuit  },
    { name: 'Extension',  href: '/extension', icon: PuzzleIcon    },
    { name: 'About',      href: '/about',     icon: Info          },
];

export default function Navbar() {
    const pathname = usePathname();

    return (
        <nav className="fixed top-0 left-0 w-full z-50 px-6 py-3 flex justify-center">
            {/* pill card — wide enough to hold 3 cols: logo | links | cta */}
            <div className="w-full max-w-3xl grid grid-cols-[auto_1fr_auto] items-center glass-card px-5 py-2 border-white/5 bg-black/50 backdrop-blur-2xl">

                {/* ── Left: Logo + Brand ── */}
                <Link href="/" className="flex items-center gap-2.5 group">
                    <div className="relative w-9 h-9 shrink-0">
                        <Image
                            src="/logo-transparent.png"
                            alt="ZeroTrust AI Shield Logo"
                            width={72}
                            height={72}
                            quality={90}
                            className="object-contain w-full h-full drop-shadow-[0_0_6px_rgba(249,115,22,0.5)]"
                        />
                    </div>
                    <span className="text-sm font-black tracking-tight text-white leading-none">
                        Zero<span className="text-orange-500">Trust</span>{' '}
                        <span className="text-white/70">AI</span>
                    </span>
                </Link>

                {/* ── Centre: Nav links ── */}
                <div className="flex items-center justify-center gap-8">
                    {NAV_LINKS.map((item) => {
                        const isActive =
                            item.href === '/'
                                ? pathname === '/'
                                : pathname.startsWith(item.href.split('#')[0]) && item.href.split('#')[0] !== '/';
                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                className={`group flex items-center gap-1.5 text-[10px] uppercase tracking-widest font-black transition-colors duration-200 ${
                                    isActive
                                        ? 'text-orange-500'
                                        : 'text-white/40 hover:text-orange-500'
                                }`}
                            >
                                <item.icon
                                    size={11}
                                    className={isActive ? 'text-orange-500' : 'group-hover:text-orange-500 transition-colors'}
                                />
                                {item.name}
                                {isActive && (
                                    <span className="w-1 h-1 rounded-full bg-orange-500 ml-0.5" />
                                )}
                            </Link>
                        );
                    })}
                </div>

                {/* ── Right: spacer to keep links centred ── */}
                <div className="w-9" />

            </div>
        </nav>
    );
}
