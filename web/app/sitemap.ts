import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = "https://cultivosagro.com";
  const lastModified = new Date();
  return [
    {
      url: `${base}/`,
      lastModified,
      changeFrequency: "weekly",
      priority: 1,
      alternates: {
        languages: {
          en: `${base}/`,
          es: `${base}/?lang=es`,
        },
      },
    },
    {
      url: `${base}/?lang=es`,
      lastModified,
      changeFrequency: "weekly",
      priority: 0.9,
    },
  ];
}
