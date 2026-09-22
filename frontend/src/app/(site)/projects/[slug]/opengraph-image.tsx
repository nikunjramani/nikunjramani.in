import { ImageResponse } from "next/og";

import { getProjectBySlug } from "@/lib/data/projects";

export const alt = "Project preview";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const project = await getProjectBySlug(slug);

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px",
          background: "#0a0a0a",
          color: "#fafafa",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", fontSize: 28, color: "#a3a3a3", marginBottom: 24 }}>
          nikunjramani.in
        </div>
        <div style={{ display: "flex", fontSize: 64, fontWeight: 600, lineHeight: 1.15 }}>
          {project?.title ?? "Project"}
        </div>
        {project?.summary ? (
          <div style={{ display: "flex", fontSize: 32, color: "#a3a3a3", marginTop: 24, maxWidth: 900 }}>
            {project.summary}
          </div>
        ) : null}
      </div>
    ),
    { ...size },
  );
}
