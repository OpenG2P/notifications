"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";

const COLLAPSE_AT = 140;

export function ExpandableMessage({
  text,
  showMore,
  showLess,
}: {
  text: string;
  showMore: string;
  showLess: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const canCollapse = text.length > COLLAPSE_AT;

  return (
    <div className="mt-1">
      <p
        className={`m-0 text-[13px] leading-[1.55] text-[var(--ogp-inbox-text-muted)] sm:text-[13.5px] ${
          canCollapse && !expanded ? "line-clamp-2" : ""
        }`}
      >
        {text}
      </p>
      {canCollapse ? (
        <button
          type="button"
          aria-expanded={expanded}
          className="mt-1 inline-flex items-center gap-0.5 text-[12.5px] font-bold text-[var(--ogp-inbox-text)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ogp-inbox-accent)]"
          onClick={(e) => {
            e.stopPropagation();
            setExpanded((prev) => !prev);
          }}
        >
          {expanded ? showLess : showMore}
          <ChevronDown
            size={13}
            strokeWidth={2.2}
            className={`transition-transform duration-150 ${expanded ? "rotate-180" : ""}`}
          />
        </button>
      ) : null}
    </div>
  );
}
