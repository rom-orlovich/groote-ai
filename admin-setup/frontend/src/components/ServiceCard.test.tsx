import { render, screen } from "@testing-library/react";
import { act } from "react";
import { describe, expect, it } from "vitest";
import { ConfigSummary } from "./ServiceCard";

describe("ConfigSummary", () => {
  it("renders title and CONFIGURED badge", async () => {
    await act(async () => {
      render(
        <ConfigSummary
          title="GITHUB APP"
          status="configured"
          configs={[
            { key: "GITHUB_APP_ID", value: "2811726", category: "github", is_masked: false },
          ]}
        />,
      );
    });
    expect(screen.getByText("GITHUB APP")).toBeInTheDocument();
    expect(screen.getByText("CONFIGURED")).toBeInTheDocument();
  });

  it("renders SKIPPED badge and hides config values", async () => {
    await act(async () => {
      render(<ConfigSummary title="JIRA / ATLASSIAN" status="skipped" configs={[]} />);
    });
    expect(screen.getByText("SKIPPED")).toBeInTheDocument();
  });

  it("renders masked sensitive values", async () => {
    await act(async () => {
      render(
        <ConfigSummary
          title="GITHUB APP"
          status="configured"
          configs={[
            {
              key: "GITHUB_CLIENT_SECRET",
              value: "••••••T2E",
              category: "github",
              is_masked: true,
            },
          ]}
        />,
      );
    });
    expect(screen.getByText("••••••T2E")).toBeInTheDocument();
    expect(screen.getByText("GITHUB_CLIENT_SECRET")).toBeInTheDocument();
  });

  it("renders non-sensitive values in full", async () => {
    await act(async () => {
      render(
        <ConfigSummary
          title="GITHUB APP"
          status="configured"
          configs={[
            { key: "GITHUB_APP_ID", value: "2811726", category: "github", is_masked: false },
          ]}
        />,
      );
    });
    expect(screen.getByText("2811726")).toBeInTheDocument();
  });
});
