"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/stores/authStore";
import { useStudentStore } from "@/lib/stores/studentStore";
import { progressAPI, notesAPI } from "@/lib/api";
import type { Note, Revision, ProgressStats } from "@/lib/types";
import { BookOpen, Target, TrendingUp, Calendar, Zap, Award, ChevronRight, Home, Settings, LogOut, Menu, X } from "lucide-react";
import { ReadinessGauge } from "@/components/features/ReadinessGauge";
import { RevisionCard } from "@/components/features/RevisionCard";
import { RecentNoteCard } from "@/components/features/RecentNoteCard";
import { QuickAskBar } from "@/components/features/QuickAskBar";

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();
  const { profile, progress, recentNotes, revisions, setProgress, setRecentNotes, setRevisions } = useStudentStore();
  const [greeting, setGreeting] = useState("Good morning");
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (profile && !profile.onboarding_complete) {
      router.push("/onboarding");
      return;
    }
    if (isAuthenticated) loadDashboard();
  }, [isAuthenticated]);

  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 12) setGreeting("Good morning");
    else if (hour < 17) setGreeting("Good afternoon");
    else setGreeting("Good evening");
  }, []);

  const loadDashboard = async () => {
    try {
      const [progressData, notesData, revisionData] = await Promise.all([
        progressAPI.getReadiness(),
        notesAPI.list({ limit: 4 }),
        progressAPI.getRevisions(),
      ]);
      setProgress(progressData.data);
      setRecentNotes(notesData.data?.notes || []);
      setRevisions(revisionData.data?.revisions || []);
    } catch (err) {
      console.error("Dashboard load error:", err);
    } finally {
      setLoading(false);
    }
  };

  const examDate = profile?.exam_dates?.[profile?.exam_targets?.[0]];
  const daysLeft = examDate
    ? Math.ceil((new Date(examDate).getTime() - Date.now()) / 86400000)
    : null;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: "#0F0B1E" }}>
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-textBody font-caveat text-lg">Loading your study dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen" style={{ backgroundColor: "#0F0B1E" }}>
      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-40 w-64 transform transition-transform md:static md:transform-none ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
        style={{ backgroundColor: "#1A0F3C" }}
      >
        <div className="flex flex-col h-full p-6">
          {/* Logo */}
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-2xl font-bold gradient-text">EkalavyaAI</h1>
            <button
              onClick={() => setSidebarOpen(false)}
              className="md:hidden text-textLight hover:text-orange transition-colors"
            >
              <X size={20} />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-3">
            {[
              { href: "/dashboard", icon: Home, label: "Dashboard", active: true },
              { href: "/notes", icon: BookOpen, label: "Generate Notes" },
              { href: "/chat", icon: Zap, label: "Ask AI Doubts" },
              { href: "/practice", icon: Target, label: "PYQ Practice" },
              { href: "/progress", icon: TrendingUp, label: "Progress Analytics" },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg transition-all"
                  style={{
                    backgroundColor: item.active ? "rgba(249, 115, 22, 0.2)" : "transparent",
                    color: item.active ? "#F97316" : "#E5E7EB",
                  }}
                  onMouseEnter={(e) => {
                    if (!item.active) e.currentTarget.style.backgroundColor = "rgba(255,255,255,0.05)";
                  }}
                  onMouseLeave={(e) => {
                    if (!item.active) e.currentTarget.style.backgroundColor = "transparent";
                  }}
                >
                  <Icon size={20} />
                  <span className="font-medium text-sm">{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="space-y-3 border-t border-purple/30 pt-4">
            <Link
              href="/settings"
              className="flex items-center gap-3 px-4 py-3 rounded-lg text-textBody hover:bg-card-dark-hover transition-colors"
            >
              <Settings size={20} />
              <span className="text-sm">Settings</span>
            </Link>
            <button
              onClick={() => {
                logout();
                router.push("/auth/login");
              }}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-textBody hover:text-orange transition-colors hover:bg-card-dark-hover"
            >
              <LogOut size={20} />
              <span className="text-sm">Logout</span>
            </button>
          </div>
        </div>

        {/* Sidebar overlay on mobile */}
        {sidebarOpen && (
          <button
            className="fixed inset-0 z-30 md:hidden"
            onClick={() => setSidebarOpen(false)}
            style={{ backgroundColor: "rgba(0,0,0,0.5)" }}
          />
        )}
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <div
          className="h-16 border-b flex items-center justify-between px-6"
          style={{ backgroundColor: "#1A0F3C", borderColor: "rgba(255,255,255,0.1)" }}
        >
          <button
            onClick={() => setSidebarOpen(true)}
            className="md:hidden text-textLight hover:text-orange transition-colors"
          >
            <Menu size={24} />
          </button>
          <h2 className="text-textLight font-caveat text-2xl flex-1 ml-4 md:ml-0">
            {greeting}, {user?.name?.split(" ")[0]}!
          </h2>
          <div className="flex items-center gap-4">
            {daysLeft !== null && (
              <div className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-lg" style={{ backgroundColor: "rgba(249, 115, 22, 0.1)" }}>
                <Zap size={18} style={{ color: "#F97316" }} />
                <span className="text-sm font-semibold" style={{ color: "#F97316" }}>
                  {daysLeft} days left
                </span>
              </div>
            )}
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white text-sm"
              style={{ backgroundColor: "#F97316" }}
            >
              {user?.name?.[0]?.toUpperCase()}
            </div>
          </div>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-auto">
          <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
            {/* Exam Countdown - Prominent */}
            {daysLeft !== null && (
              <div
                className="rounded-2xl p-8 text-center card-interactive"
                style={{
                  backgroundColor: "rgba(249, 115, 22, 0.1)",
                  borderLeft: "4px solid #F97316",
                }}
              >
                <p className="text-textMuted text-sm mb-2">Exam Countdown</p>
                <h3 className="text-5xl font-bold gradient-text mb-2">{daysLeft}</h3>
                <p className="text-lg text-textBody">
                  {daysLeft === 1 ? "day left" : "days left"} until your{" "}
                  <span className="font-semibold" style={{ color: "#F97316" }}>
                    {profile?.exam_targets?.[0]?.replace("_", " ")}
                  </span>{" "}
                  exam
                </p>
              </div>
            )}

            {/* Stats Row */}
            <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { icon: BookOpen, label: "Chapters Studied", value: progress?.chapters_studied || 0, color: "#4C1D95" },
                { icon: Target, label: "PYQ Solved", value: progress?.pyq_solved || 0, color: "#F97316" },
                { icon: Zap, label: "Day Streak", value: profile?.login_streak || 0, color: "#FBBF24" },
                { icon: Award, label: "Credits", value: progress?.credits || 0, color: "#4C1D95" },
              ].map((stat) => {
                const Icon = stat.icon;
                return (
                  <div
                    key={stat.label}
                    className="rounded-xl p-6 card-interactive"
                    style={{ backgroundColor: "rgba(255,255,255,0.05)", borderLeft: `4px solid ${stat.color}` }}
                  >
                    <Icon size={24} style={{ color: stat.color }} className="mb-3" />
                    <div className="text-3xl font-bold text-textLight mb-1">{String(stat.value)}</div>
                    <div className="text-xs text-textMuted">{stat.label}</div>
                  </div>
                );
              })}
            </section>

            {/* Main Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left: Readiness + Quick Actions */}
              <div className="lg:col-span-1 space-y-4">
                <ReadinessGauge
                  score={typeof progress?.readiness_score === "number" ? progress.readiness_score : 0}
                  exam={profile?.exam_targets?.[0] || "CA_FOUNDATION"}
                />

                {/* Quick Actions */}
                <div
                  className="rounded-xl p-6 glass-card"
                  style={{ backgroundColor: "rgba(255,255,255,0.05)" }}
                >
                  <h3 className="font-semibold text-textLight mb-4">Quick Actions</h3>
                  <div className="space-y-2">
                    {[
                      { href: "/notes", emoji: "📝", label: "Generate Notes" },
                      { href: "/chat", emoji: "💬", label: "Ask AI" },
                      { href: "/practice", emoji: "🎯", label: "PYQ Practice" },
                      { href: "/progress", emoji: "📊", label: "Analytics" },
                    ].map((action) => (
                      <Link
                        key={action.href}
                        href={action.href}
                        className="flex items-center justify-between p-3 rounded-lg transition-all hover:bg-card-dark-hover"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-xl">{action.emoji}</span>
                          <span className="text-sm font-medium text-textBody">{action.label}</span>
                        </div>
                        <ChevronRight size={14} style={{ color: "#9CA3AF" }} />
                      </Link>
                    ))}
                  </div>
                </div>
              </div>

              {/* Right: Revisions + Recent Notes */}
              <div className="lg:col-span-2 space-y-6">
                {/* Due Revisions */}
                {revisions && revisions.length > 0 && (
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="font-semibold text-textLight flex items-center gap-2">
                        <Calendar size={18} style={{ color: "#F97316" }} />
                        Today's Revision
                      </h2>
                      <Link href="/progress" className="text-xs text-orange hover:underline">
                        See all →
                      </Link>
                    </div>
                    <div className="grid sm:grid-cols-2 gap-3">
                      {(revisions as Revision[]).slice(0, 2).map((rev) => (
                        <RevisionCard key={rev.id} revision={rev} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Recent Notes */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="font-semibold text-textLight flex items-center gap-2">
                      <BookOpen size={18} style={{ color: "#4C1D95" }} />
                      Recent Notes
                    </h2>
                    <Link href="/notes" className="text-xs text-orange hover:underline">
                      View all →
                    </Link>
                  </div>
                  {recentNotes && recentNotes.length > 0 ? (
                    <div className="grid sm:grid-cols-2 gap-3">
                      {(recentNotes as Note[]).slice(0, 2).map((note) => (
                        <RecentNoteCard key={note.id} note={note} />
                      ))}
                    </div>
                  ) : (
                    <div
                      className="rounded-xl p-8 text-center glass-card"
                      style={{ backgroundColor: "rgba(249, 115, 22, 0.05)" }}
                    >
                      <p className="text-textMuted font-caveat text-lg mb-4">
                        No notes yet — let's generate your first chapter!
                      </p>
                      <Link
                        href="/notes"
                        className="inline-flex items-center gap-2 btn-orange"
                      >
                        <Zap size={16} /> Generate First Notes
                      </Link>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
