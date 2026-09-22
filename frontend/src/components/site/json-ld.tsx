/**
 * JSON.stringify escapes `<` as `<` isn't automatic, and a raw `</script>` inside the
 * payload would close the tag early — this is the one place structured data touches the DOM,
 * so it's the one place that needs the escape.
 */
export function JsonLd({ data }: { data: object }) {
  const json = JSON.stringify(data).replace(/</g, "\\u003c");
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: json }} />;
}
