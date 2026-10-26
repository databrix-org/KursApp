"use client";
import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useLocale } from "next-intl";
import { useTheme } from "next-themes";
import {
  BookOpen,
  LifeBuoy,
  Shield,
  UserRound,
  SunMoon,
  LogOut,
  GraduationCap,
} from "lucide-react";
import {
  Sidebar,
  SidebarProvider,
  SidebarContent,
  SidebarHeader,
  SidebarFooter,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarTrigger,
  SidebarInset,
  useSidebar,
} from "@repo/design-system/components/ui/sidebar";
import { Button } from "@repo/design-system/components/ui/button";
import { Separator } from "@repo/design-system/components/ui/separator";
import { mutate, type User } from "@repo/api-client";
import { useText } from "@/lib/hooks";
import { UserProvider } from "./providers";
export function Shell({
  user,
  children,
}: {
  user: User;
  children: React.ReactNode;
}) {
  const t = useText(),
    locale = useLocale(),
    path = usePathname(),
    router = useRouter(),
    { theme, setTheme } = useTheme();
  const links = [
    { href: "courses", label: t.courses, icon: BookOpen },
    { href: "submissions", label: t.submissions, icon: GraduationCap },
    { href: "support", label: t.support, icon: LifeBuoy },
    { href: "profile", label: t.profile, icon: UserRound },
    ...(user.is_admin ? [{ href: "admin", label: t.admin, icon: Shield }] : []),
  ];
  return (
    <UserProvider user={user}>
      <SidebarProvider>
        <CloseOnNavigation />
        <Sidebar>
          <nav aria-label={t.learning} className="flex h-full flex-col">
            <SidebarHeader className="px-5 py-7">
              <Link
                href={`/${locale}/courses`}
                className="text-xl font-bold tracking-tight"
              >
                databrix<span className="text-primary">.</span>
              </Link>
              <p className="mt-2 text-xs text-muted-foreground">{t.welcome}</p>
            </SidebarHeader>
            <SidebarContent>
              <SidebarMenu className="px-3">
                {links.map(({ href, label, icon: Icon }) => (
                  <SidebarMenuItem key={href}>
                    <SidebarMenuButton
                      asChild
                      isActive={path.includes("/" + href)}
                    >
                      <Link href={`/${locale}/${href}`}>
                        <Icon />
                        {label}
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarContent>
            <SidebarFooter className="p-5">
              <p className="text-sm font-medium">
                {user.first_name} {user.last_name}
              </p>
              <p className="truncate text-xs text-muted-foreground">
                {user.email}
              </p>
              <Separator className="my-3" />
              <Button
                variant="ghost"
                onClick={async () => {
                  await mutate("session/change/", {}, "DELETE");
                  router.push(`/${locale}/login`);
                  router.refresh();
                }}
              >
                <LogOut />
                {t.logout}
              </Button>
            </SidebarFooter>
          </nav>
        </Sidebar>
        <SidebarInset>
          <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b bg-background/95 px-6 backdrop-blur">
            <SidebarTrigger />
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  const next = locale === "de" ? "en" : "de";
                  document.cookie = `locale=${next}; Path=/; SameSite=Lax`;
                  router.push(path.replace(/^\/(de|en)/, `/${next}`));
                }}
              >
                {locale === "de" ? "English" : "Deutsch"}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                aria-label="Theme"
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              >
                <SunMoon />
              </Button>
            </div>
          </header>
          <main
            id="main-content"
            className="mx-auto w-full max-w-7xl p-5 sm:p-10"
          >
            {children}
          </main>
        </SidebarInset>
      </SidebarProvider>
    </UserProvider>
  );
}

function CloseOnNavigation() {
  const path = usePathname(),
    { setOpenMobile } = useSidebar();
  useEffect(() => setOpenMobile(false), [path, setOpenMobile]);
  return null;
}
