"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ContactMessageSchema } from "@/generated/schemas.zod";
import { submitContact } from "@/site/lib/contact";
import { getAppCheckToken, initAppCheck } from "@/site/lib/app-check";
import { buttonPrimary } from "@/site/components/styles";
import { cn } from "@/lib/utils";

const label = "font-mono text-xs text-muted-foreground";
const field =
  "w-full rounded-(--radius) border border-border bg-surface px-3 py-2.5 text-base transition-colors hover:border-muted-foreground focus-visible:border-accent focus-visible:outline-2 focus-visible:outline-accent aria-invalid:border-danger";

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
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(FormSchema) });

  // Start App Check while the visitor types, so reCAPTCHA has signals to score by submit.
  useEffect(() => {
    void initAppCheck();
  }, []);

  async function onSubmit(values: FormValues) {
    setStatus("submitting");
    try {
      await submitContact(
        {
          ...values,
          // Honeypot stays empty for real users; a bot filling every field trips it server-side.
          honeypot: values.honeypot ?? "",
        },
        await getAppCheckToken(),
      );
      setStatus("success");
      reset();
    } catch {
      setStatus("error");
    }
  }

  if (status === "success") {
    return (
      <div className="border-l-2 border-accent bg-surface p-6" role="status">
        <p className="font-semibold font-stretch-112%">Message sent.</p>
        <p className="mt-1 text-sm text-muted-foreground">Thanks for writing. I&apos;ll reply by email.</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-6" noValidate>
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
        <label htmlFor="name" className={label}>
          Name
        </label>
        <input
          id="name"
          type="text"
          autoComplete="name"
          aria-invalid={errors.name ? true : undefined}
          aria-describedby={errors.name ? "name-error" : undefined}
          className={field}
          {...register("name")}
        />
        {errors.name ? <p id="name-error" className="text-xs text-danger">{errors.name.message}</p> : null}
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="email" className={label}>
          Email
        </label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          spellCheck={false}
          aria-invalid={errors.email ? true : undefined}
          aria-describedby={errors.email ? "email-error" : undefined}
          className={field}
          {...register("email")}
        />
        {errors.email ? <p id="email-error" className="text-xs text-danger">{errors.email.message}</p> : null}
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="subject" className={label}>
          Subject <span className="text-muted-foreground">(optional)</span>
        </label>
        <input
          id="subject"
          type="text"
          className={field}
          {...register("subject")}
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="message" className={label}>
          Message
        </label>
        <textarea
          id="message"
          rows={7}
          aria-invalid={errors.message ? true : undefined}
          aria-describedby={errors.message ? "message-error" : undefined}
          className={field}
          {...register("message")}
        />
        {errors.message ? <p id="message-error" className="text-xs text-danger">{errors.message.message}</p> : null}
      </div>

      {/* Safety net: a resolver error that isn't on name/email/message (a root-level Zod
          issue, say) would otherwise be silently swallowed — the exact failure mode this
          form shipped with once already. Surface anything unaccounted for rather than
          trust the known fields to cover every case forever. */}
      {Object.entries(errors)
        .filter(([key]) => !["name", "email", "message", "subject", "honeypot"].includes(key))
        .map(([key, err]) => (
          <p key={key} className="text-sm text-danger">
            {err?.message?.toString() ?? "Please check the form and try again."}
          </p>
        ))}

      {status === "error" ? (
        <p className="text-sm text-danger" role="alert">The message didn&apos;t send. Check your connection and try again.</p>
      ) : null}

      <button
        type="submit"
        disabled={status === "submitting"}
        className={cn(buttonPrimary, "w-fit", status === "submitting" && "opacity-70")}
      >
        {status === "submitting" ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : null}
        {status === "submitting" ? "Sending…" : "Send message"}
      </button>
    </form>
  );
}
