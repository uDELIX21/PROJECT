import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "School Management System",
    short_name: "SMS",
    description: "School Management Information System",
    start_url: "/",
    display: "standalone",
    background_color: "#f8fafc",
    theme_color: "#16603e",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
  };
}
