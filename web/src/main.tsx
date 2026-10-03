// Yazı tipleri pakete gömülü (internetsiz depo ağında da çalışsın). Türkçe karakterler latin-ext'te.
import "@fontsource/big-shoulders-display/latin-700";
import "@fontsource/big-shoulders-display/latin-ext-700";
import "@fontsource/big-shoulders-display/latin-800";
import "@fontsource/big-shoulders-display/latin-ext-800";
import "@fontsource/ibm-plex-sans/latin-400";
import "@fontsource/ibm-plex-sans/latin-ext-400";
import "@fontsource/ibm-plex-sans/latin-500";
import "@fontsource/ibm-plex-sans/latin-ext-500";
import "@fontsource/ibm-plex-sans/latin-600";
import "@fontsource/ibm-plex-sans/latin-ext-600";
import "@fontsource/ibm-plex-mono/latin-400";
import "@fontsource/ibm-plex-mono/latin-ext-400";
import "@fontsource/ibm-plex-mono/latin-500";
import "@fontsource/ibm-plex-mono/latin-ext-500";
import "./styles.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
