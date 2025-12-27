"use client";

import dynamic from "next/dynamic";
import MainSection from "@/src/components/sections/MainSection";
import { weddingConfig } from "@/src/config/wedding-config";
import { ToastProvider } from "@/src/components/ui/ToastProvider";
import QuickActionsBar from "@/src/components/ui/QuickActionsBar";

const InvitationSection = dynamic(() => import("@/src/components/sections/InvitationSection"));
const DateSection = dynamic(() => import("@/src/components/sections/DateSection"));
const VenueSection = dynamic(() => import("@/src/components/sections/VenueSection"), { ssr: false });
const GallerySection = dynamic(() => import("@/src/components/sections/GallerySection"));
const RsvpSection = dynamic(() => import("@/src/components/sections/RsvpSection"));
const AccountSection = dynamic(() => import("@/src/components/sections/AccountSection"));
const Footer = dynamic(() => import("@/src/components/sections/Footer"));

export default function Home() {
  const showRsvp = weddingConfig.rsvp?.enabled ?? true;
  const galleryPosition = weddingConfig.gallery.position || "middle";

  return (
    <ToastProvider>
      <main>
        <MainSection />
        <InvitationSection />
        <DateSection />
        <VenueSection />
        {galleryPosition === "middle" && <GallerySection />}
        {showRsvp && <RsvpSection />}
        <AccountSection />
        {galleryPosition === "bottom" && <GallerySection />}
        <Footer />

        {/* 하단 고정 퀵 액션 */}
        <QuickActionsBar />
      </main>
    </ToastProvider>
  );
}
