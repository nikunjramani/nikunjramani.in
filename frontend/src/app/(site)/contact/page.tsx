import type { Metadata } from "next";

import { ContactForm } from "@/site/components/contact-form";
import { Container, SpecTable } from "@/site/components/spec";
import { getProfile } from "@/lib/data/profile";

export const metadata: Metadata = {
  title: "Contact",
  description: "Get in touch.",
  alternates: { canonical: "/contact" },
};

export default async function ContactPage() {
  const profile = await getProfile();

  return (
    <Container>
      <div className="grid gap-12 pt-16 sm:pt-20 lg:grid-cols-[1fr_minmax(0,34rem)] lg:gap-16">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight font-stretch-125% text-balance sm:text-[2.75rem] sm:leading-[1.05]">
            Get in touch
          </h1>
          <p className="mt-4 max-w-md text-lg text-muted-foreground text-pretty">
            {profile?.availableForWork
              ? "Have a project in mind? I'd love to hear about it."
              : "Send a message and I'll get back to you when I can."}
          </p>
          <SpecTable
            className="mt-10 max-w-md"
            rows={[
              profile?.availableForWork && { key: "Status", value: "Available for work" },
              profile?.location && { key: "Based in", value: profile.location },
            ]}
          />
        </div>

        <ContactForm />
      </div>
    </Container>
  );
}
