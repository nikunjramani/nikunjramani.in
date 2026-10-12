"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ContactMessageSchema } from "@/generated/schemas.zod";
import { Turnstile } from "@/components/site/turnstile";
import { cn } from "@/lib/utils";

// ContactMessageSchema is `.strict()` (ADR: server-set fields can never be client-supplied),
// and `.pick()` carries that strictness into the picked schema too — so the honeypot field,
// which react-hook-form always includes in the submitted values once registered, has to be
// declared here or every real submission fails resolver validation with an "unrecognized
// key" error that attaches to the form root, not any field, and never renders anywhere.
// Reproduced directly: with .pick() alone, a filled-out form silently fails to submit with
// zero visible feedback — no success, no error, no progress.
const FormSchema = ContactMessageSchema.pick({
  name: true,
  email: true,
  subject: true,
  message: true,
}).extend({ honeypot: z.string().optional() });
type FormValues = z.infer<typeof FormSchema>;

type Status = "idle" | "submitting" | "success" | "error";

export function ContactForm() {
  const [status, setStatus] = useState<Status>("idle");
  const [turnstileToken, setTurnstileToken] = useState("");
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(FormSchema) });

  async function onSubmit(values: FormValues) {
    setStatus("submitting");
    try {
      const res = await fetch("/api/v1/contact/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // honeypot stays empty for real users — a bot filling every field trips it server-side.
        body: JSON.stringify({ ...values, honeypot: values.honeypot ?? "", turnstileToken }),
      });
      if (!res.ok) throw new Error(`status ${res.status}`);
      setStatus("success");
      reset();
    } catch {
      setStatus("error");
    }
  }

  if (status === "success") {
    return (
      <div className="rounded-lg border border-border bg-surface p-6 text-center">
        <p className="font-medium">Thanks — I&apos;ll get back to you soon.</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5" noValidate>
      {/* Honeypot: invisible to real visitors, irresistible to naive bots that fill every field. */}
      <input
        type="text"
        tabIndex={-1}
        autoComplete="off"
        aria-hidden="true"
        className="absolute h-0 w-0 opacity-0"
        {...register("honeypot")}
      />

      <div className="flex flex-col gap-1.5">
        <label htmlFor="name" className="text-sm font-medium">
          Name
        </label>
        <input
          id="name"
          type="text"
          className="rounded-md border border-border bg-background px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-accent"
          {...register("name")}
        />
        {errors.name ? <p className="text-xs text-red-500">{errors.name.message}</p> : null}
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="email" className="text-sm font-medium">
          Email
        </label>
        <input
          id="email"
          type="email"
          className="rounded-md border border-border bg-background px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-accent"
          {...register("email")}
        />
        {errors.email ? <p className="text-xs text-red-500">{errors.email.message}</p> : null}
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="subject" className="text-sm font-medium">
          Subject <span className="text-muted-foreground">(optional)</span>
        </label>
        <input
          id="subject"
          type="text"
          className="rounded-md border border-border bg-background px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-accent"
          {...register("subject")}
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="message" className="text-sm font-medium">
          Message
        </label>
        <textarea
          id="message"
          rows={6}
          className="rounded-md border border-border bg-background px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-accent"
          {...register("message")}
        />
        {errors.message ? <p className="text-xs text-red-500">{errors.message.message}</p> : null}
      </div>

      <Turnstile onVerify={setTurnstileToken} />

      {/* Safety net: a resolver error that isn't on name/email/message (a root-level Zod
          issue, say) would otherwise be silently swallowed — the exact failure mode this
          form shipped with once already. Surface anything unaccounted for rather than
          trust the known fields to cover every case forever. */}
      {Object.entries(errors)
        .filter(([key]) => !["name", "email", "message", "subject", "honeypot"].includes(key))
        .map(([key, err]) => (
          <p key={key} className="text-sm text-red-500">
            {err?.message?.toString() ?? "Please check the form and try again."}
          </p>
        ))}

      {status === "error" ? (
        <p className="text-sm text-red-500">Something went wrong — please try again in a moment.</p>
      ) : null}

      <button
        type="submit"
        disabled={status === "submitting"}
        className={cn(
          "inline-flex w-fit items-center gap-1.5 rounded-md bg-accent px-4 py-2 text-sm text-accent-foreground transition-opacity hover:opacity-90",
          status === "submitting" && "opacity-70",
        )}
      >
        {status === "submitting" ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
        Send message
      </button>
    </form>
  );
}
