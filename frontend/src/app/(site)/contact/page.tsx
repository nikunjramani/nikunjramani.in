import type { Metadata } from "next";

import { ContactForm } from "@/components/site/contact-form";
import { getProfile } from "@/lib/data/profile";

export const metadata: Metadata = {
  title: "Contact",
  description: "Get in touch.",
};

export default async function ContactPage() {
  const profile = await getProfile();

  return (
    <div className="mx-auto max-w-lg px-6 py-16">
      <h1 className="mb-2 text-2xl font-semibold tracking-tight">Get in touch</h1>
      <p className="mb-8 text-muted-foreground">
        {profile?.availableForWork
          ? "Have a project in mind? I'd love to hear about it."
          : "Send a message and I'll get back to you when I can."}
      </p>
      <ContactForm />
    </div>
  );
}
