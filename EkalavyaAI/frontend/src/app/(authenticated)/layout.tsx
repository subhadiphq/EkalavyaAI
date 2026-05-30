"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";
import {
  LayoutDashboard, BookOpen, MessageCircle, Target,
  TrendingUp, CreditCard, Menu, X, LogOut, ChevronRight, Bell,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard",   icon: LayoutDashboard },
  { href: "/notes",     label: "Notes",        icon: BookOpen        },
  { href: "/chat",      label: "Ask a Doubt",  icon: MessageCircle   },
  { href: "/practice",  label: "Practice PYQ", icon: Target          },
  { href: "/progress",  label: "My Progress",  icon: TrendingUp      },
  { href: "/pricing",   label: "Upgrade Plan", icon: CreditCard      },
];

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) router.push("/auth/login?redirect=" + encodeURIComponent(pathname));
  }, [isAuthenticated]);

  const handleLogout = () => { logout(); router.push("/"); };

  if (!isAuthenticated) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  const NavContent = () => (
    <>
      <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link key={href} href={href} onClick={() => setMobileOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all
                ${active
                  ? "bg-blue-50 text-blue-700 shadow-sm"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"}`}>
              <Icon size={17} className={active ? "text-blue-600" : "text-slate-400"} />
              <span className="flex-1">{label}</span>
              {active && <ChevronRight size={13} className="text-blue-400" />}
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t border-slate-100">
        <div className="flex items-center gap-3 px-3 py-2 mb-1 rounded-xl">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 text-white flex items-center justify-center font-bold text-sm shrink-0">
            {user?.name?.[0]?.toUpperCase() ?? "S"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-slate-800 truncate">{user?.name}</p>
            <p className="text-xs text-slate-400 truncate">{user?.email}</p>
          </div>
        </div>
        <button onClick={handleLogout}
          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors mt-1">
          <LogOut size={14} /> Sign out
        </button>
      </div>
    </>
  );

  return (
    <div className="min-h-screen bg-slate-50 flex">

      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex flex-col w-60 bg-white border-r border-slate-100 fixed inset-y-0 left-0 z-30">
        <div className="flex items-center gap-2 px-5 h-16 border-b border-slate-100 shrink-0">
          <span className="font-bold text-blue-700 text-xl">EkalavyaAI</span>
          <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full font-semibold">
            {user?.plan}
          </span>
        </div>
        <NavContent />
      </aside>

      {/* Mobile Top Bar */}
      <div className="lg:hidden fixed top-0 inset-x-0 z-40 h-14 bg-white border-b border-slate-100 flex items-center justify-between px-4">
        <span className="font-bold text-blue-700 text-lg">EkalavyaAI</span>
        <div className="flex items-center gap-2">
          <button className="p-1.5 hover:bg-slate-100 rounded-full">
            <Bell size={18} className="text-slate-500" />
          </button>
          <button onClick={() => setMobileOpen(true)} className="p-1.5 hover:bg-slate-100 rounded-lg">
            <Menu size={22} className="text-slate-700" />
          </button>
        </div>
      </div>

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <div className="relative w-72 bg-white h-full flex flex-col shadow-2xl animate-in slide-in-from-left duration-200">
            <div className="flex items-center justify-between px-5 h-14 border-b border-slate-100 shrink-0">
              <span className="font-bold text-blue-700 text-lg">EkalavyaAI</span>
              <button onClick={() => setMobileOpen(false)} className="p-1.5 hover:bg-slate-100 rounded-lg">
                <X size={18} className="text-slate-500" />
              </button>
            </div>
            <NavContent />
          </div>
        </div>
      )}

      {/* Page Content */}
      <main className="flex-1 lg:ml-60 pt-14 lg:pt-0 min-h-screen overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
