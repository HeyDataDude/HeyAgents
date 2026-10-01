import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PriorityBadge, StatusBadge } from "./badges";

describe("StatusBadge", () => {
  it("renders humanized status text", () => {
    render(<StatusBadge status="waiting_for_user" />);
    expect(screen.getByText("waiting for user")).toBeInTheDocument();
  });
});

describe("PriorityBadge", () => {
  it("renders the priority label", () => {
    render(<PriorityBadge priority="high" />);
    expect(screen.getByText("high")).toBeInTheDocument();
  });
});
