import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function Markdown({ children }: { children: string }) {
  return (
    <div className="flex flex-col gap-4 text-pretty text-foreground [&_a]:underline [&_a]:decoration-accent [&_a]:underline-offset-4 [&_code]:font-mono [&_code]:text-[0.9em] [&_ol]:list-decimal [&_ol]:pl-5 [&_strong]:font-semibold [&_ul]:list-[square] [&_ul]:pl-5 [&_li]:marker:text-accent">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  );
}
