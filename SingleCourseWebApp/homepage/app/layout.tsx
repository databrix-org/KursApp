import '../styles/globals.css'

import type { Metadata } from 'next'
import { cn } from '@/library/utils'
import { fontMedium, fontSemiBold, fontBold } from '@/library/fonts'
import { LegalFooter } from '@/components/sections/footer'

export const metadata: Metadata = {
  title: 'Create Next App',
  description: 'Generated by create next app',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body
        className={cn(
          "bg-background min-h-screen scroll-smooth font-medium antialiased [font-feature-settings:'ss01']",
          fontMedium.variable,
          fontSemiBold.variable,
          fontBold.variable,
        )}
      >
        {children}
        <LegalFooter />
      </body>
    </html>
  )
}
