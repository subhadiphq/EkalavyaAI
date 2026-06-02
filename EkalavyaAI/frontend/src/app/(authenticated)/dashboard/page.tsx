"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/stores/authStore";
import { useStudentStore } from "@/lib/stores/studentStore";
import { progressAPI, notesAPI } from "@/lib/api";
import type { Note, Revision, ProgressStats } from "@/lib/types";
import { BookOpen, Target, TrendingUp, Calendar, Zap, Award, ChevronRight } from "lucide-react";
import { ReadinessGauge } from "@/components/features/ReadinessGauge";
import { RevisionCard } from "@/components/features/RevisionCard";
import { RecentNoteCard } from "@/components/features/RecentNoteCard";
import { QuickAskBar } from "@/components/features/QuickAskBar";

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const { profile, progress, recentNotes, revisions, setProgress, setRecentNotes, setRevisions } = useStudentStore();
  const [greeting, setGreeting] = useState("Good morning");
  const [loading, setLoading] = useState(true);

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
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-600 font-caveat text-lg">Loading your study dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">


      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* Greeting + Quick Ask */}
        <section>
          <h1 className="font-caveat text-3xl text-slate-800 mb-1">
            {greeting}, {user?.name?.split(" ")[0]}! 👋
          </h1>
          {daysLeft !== null && (
            <p className="text-slate-500 text-sm mb-4">
              <span className="text-amber-600 font-semibold">{daysLeft} days</span> until your{" "}
              {profile?.exam_targets?.[0]?.replace("_", " ")} exam
            </p>
          )}
          <QuickAskBar exam={profile?.exam_targets?.[0] || "CA_FOUNDATION"} />
        </section>

        {/* Stats Row */}
        <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            {
              icon: <BookOpen size={20} className="text-blue-600" />,
              label: "Chapters Studied",
              value: String(progress?.chapters_studied || 0),
              bg: "bg-blue-50",
            },
            {
              icon: <Target size={20} className="text-green-600" />,
              label: "PYQ Solved",
              value: String(progress?.pyq_solved || 0),
              bg: "bg-green-50",
            },
            {
              icon: <Zap size={20} className="text-amber-600" />,
              label: "Day Streak 🔥",
              value: `${profile?.login_streak || 0} days`,
              bg: "bg-amber-50",
            },
            {
              icon: <Award size={20} className="text-purple-600" />,
              label: "Credits",
              value: String(progress?.credits || 0),
              bg: "bg-purple-50",
            },
          ].map((stat) => (
            <div key={stat.label} className={`${stat.bg} rounded-xl p-4`}>
              <div className="flex items-center gap-2 mb-2">{stat.icon}</div>
              <div className="font-bold text-2xl text-slate-800">{stat.value}</div>
              <div className="text-xs text-slate-500 mt-0.5">{stat.label}</div>
            </div>
          ))}
        </section>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Readiness + Actions */}
          <div className="lg:col-span-1 space-y-4">
            <ReadinessGauge
              score={typeof progress?.readiness_score === 'number' ? progress.readiness_score : 0}
              exam={profile?.exam_targets?.[0] || "CA_FOUNDATION"}
            />

            {/* Quick Actions */}
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <h3 className="font-semibold text-slate-700 mb-3 text-sm">Quick Actions</h3>
              <div className="space-y-2">
                {[
                  { href: "/notes", icon: "📝", label: "Generate Notes", desc: "New chapter" },
                  { href: "/practice", icon: "🎯", label: "Practice PYQ", desc: "Test yourself" },
                  { href: "/chat", icon: "💬", label: "Ask a Doubt", desc: "Get instant help" },
                  { href: "/progress", icon: "📊", label: "View Progress", desc: "Full analytics" },
                ].map((action) => (
                  <Link
                    key={action.href}
                    href={action.href}
                    className="flex items-center justify-between p-3 hover:bg-slate-50 rounded-lg group transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xl">{action.icon}</span>
                      <div>
                        <div className="text-sm font-medium text-slate-700">{action.label}</div>
                        <div className="text-xs text-slate-400">{action.desc}</div>
                      </div>
                    </div>
                    <ChevronRight
                      size={14}
                      className="text-slate-300 group-hover:text-slate-500 transition-colors"
                    />
                  </Link>
                ))}
              </div>
            </div>
          </div>

          {/* Right: Recent Notes + Revisions */}
          <div className="lg:col-span-2 space-y-6">
            {/* Due Revisions */}
            {revisions && revisions.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h2 className="font-semibold text-slate-700 flex items-center gap-2">
                    <Calendar size={16} className="text-amber-500" />
                    Due for Revision Today
                  </h2>
                  <Link href="/progress" className="text-xs text-blue-600 hover:underline">
                    See all →
                  </Link>
                </div>
                <div className="grid sm:grid-cols-2 gap-3">
                  {(revisions as Revision[]).slice(0, 4).map((rev) => (
                    <RevisionCard key={rev.id} revision={rev} />
                  ))}
                </div>
              </div>
            )}

            {/* Recent Notes */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-semibold text-slate-700 flex items-center gap-2">
                  <BookOpen size={16} className="text-blue-500" />
                  Recent Notes
                </h2>
                <Link href="/notes" className="text-xs text-blue-600 hover:underline">
                  View all →
                </Link>
              </div>
              {recentNotes && recentNotes.length > 0 ? (
                <div className="grid sm:grid-cols-2 gap-3">
                  {(recentNotes as Note[]).map((note) => (
                    <RecentNoteCard key={note.id} note={note} />
                  ))}
                </div>
              ) : (
                <div className="bg-white border border-dashed border-slate-200 rounded-xl p-8 text-center">
                  <p className="text-slate-400 font-caveat text-lg mb-3">
                    No notes yet — let's generate your first chapter!
                  </p>
                  <Link
                    href="/notes"
                    className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 transition-colors"
                  >
                    <Zap size={14} /> Generate First Notes
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
