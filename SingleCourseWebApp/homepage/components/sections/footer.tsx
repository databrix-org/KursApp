'use client'

import React from 'react'
import { Link } from 'next-view-transitions'

export function LegalFooter() {
  return (
    <footer
      className="fixed bottom-0 z-20 flex h-12 w-full flex-row items-center justify-start gap-12 bg-[#1D2B3A] px-8 md:bottom-0 md:z-10 md:h-[60px] md:px-20"
      aria-labelledby="footer-heading"
    >
      <div className="flex flex-row space-x-10 text-sm font-medium whitespace-nowrap text-white/80 md:text-lg md:leading-[60px]">
        <Link
          className="flex flex-row text-sm font-medium whitespace-nowrap text-[#c3e4ff] md:leading-[60px]"
          target="_blank"
          href="/"
        >
          Startseite
        </Link>
        <Link
          className="flex flex-row text-sm font-medium whitespace-nowrap text-[#c3e4ff] md:leading-[60px]"
          target="_blank"
          href="/imprint"
        >
          Impressum
        </Link>
        <Link
          className="flex flex-row text-sm font-medium whitespace-nowrap text-[#c3e4ff] md:leading-[60px]"
          target="_blank"
          href="/privacy-policy"
        >
          Datenschutz
        </Link>
        <Link
          className="flex flex-row text-sm font-medium whitespace-nowrap text-[#c3e4ff] md:leading-[60px]"
          target="_blank"
          href="/cookie-policy"
        >
          Cookie-Richtlinie
        </Link>
      </div>
    </footer>
  )
}
