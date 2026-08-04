const navToggle = document.querySelector(".nav-toggle");
const navigation = document.querySelector(".site-nav");

navToggle?.addEventListener("click", () => {
  const open = navToggle.getAttribute("aria-expanded") === "true";
  navToggle.setAttribute("aria-expanded", String(!open));
  navigation?.classList.toggle("is-open", !open);
});

navigation?.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    navToggle?.setAttribute("aria-expanded", "false");
    navigation.classList.remove("is-open");
  });
});

document.querySelectorAll(".journey-step > button").forEach((button) => {
  button.addEventListener("click", () => {
    const currentStep = button.closest(".journey-step");
    const content = currentStep.querySelector(".step-content");
    const isOpen = button.getAttribute("aria-expanded") === "true";

    document.querySelectorAll(".journey-step").forEach((step) => {
      step.classList.remove("is-active");
      step.querySelector("button")?.setAttribute("aria-expanded", "false");
      step.querySelector(".step-content")?.setAttribute("hidden", "");
      const indicator = step.querySelector(".step-toggle");
      if (indicator) indicator.textContent = "+";
    });

    if (!isOpen) {
      currentStep.classList.add("is-active");
      button.setAttribute("aria-expanded", "true");
      content?.removeAttribute("hidden");
      const indicator = currentStep.querySelector(".step-toggle");
      if (indicator) indicator.textContent = "−";
    }
  });
});

const tabs = [...document.querySelectorAll('[role="tab"]')];
tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((item) => {
      const selected = item === tab;
      item.setAttribute("aria-selected", String(selected));
      const panel = document.getElementById(item.getAttribute("aria-controls"));
      if (panel) panel.hidden = !selected;
    });
  });
  tab.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
    event.preventDefault();
    const direction = event.key === "ArrowRight" ? 1 : -1;
    const next = tabs[(tabs.indexOf(tab) + direction + tabs.length) % tabs.length];
    next.focus();
    next.click();
  });
});

const skillExamples = {
  "analyze-product": ["Discover", "Separates evidence from assumptions before anyone commits to building.", "Analyze whether a shared household-expense app for young families is worth building.", "A decision brief covering the target user, current alternatives, evidence, assumptions, risks, and the next cheapest learning step.", "RESEARCH FIRST — interview 8–12 couples about reconciliation failures before choosing features."],
  "shape-product": ["Discover", "Turns a broad opportunity into the smallest coherent product bet.", "Shape the first useful version of the household-expense product.", "A product brief with the core outcome, boundaries, non-goals, risks, and success signals.", "Start with shared capture, categorization, and a weekly review; defer budgets, investments, and AI advice."],
  "write-product-prd": ["Define", "Creates a build-ready agreement about outcomes, behavior, and completion.", "Write the PRD for shared expense review and approval.", "User journeys, requirement IDs, acceptance criteria, roles, edge cases, measures, and explicit non-goals.", "REQ-EXP-004 — both partners can see who changed a transaction and restore its previous category."],
  "design-product-experience": ["Design", "Maps every meaningful journey, state, and interaction before implementation.", "Design the mobile experience for reviewing this week's uncategorized expenses.", "A state-aware experience specification covering loading, empty, error, offline, success, and recovery behavior.", "A thumb-reachable review queue with optimistic actions, undo, and a clear offline state—not a shrunk desktop table."],
  "craft-distinctive-product": ["Design", "Finds an original product expression grounded in its users and domain.", "Make the expense product feel trustworthy and specific without looking like generic AI SaaS.", "A product point of view, signature interactions, domain language, mobile quality rules, and rejected AI-slop patterns.", "Use the weekly money ritual as the central motif; reject fake insights, neon gradients, card walls, and invented testimonials."],
  "design-web-system": ["Design", "Defines the technical structure, data ownership, boundaries, and recovery model.", "Design the web architecture for shared households and transaction imports.", "An architecture brief covering components, data model, APIs, permissions, observability, migrations, and failure handling.", "Household membership is enforced server-side on every transaction query; imports are idempotent and resumable."],
  "threat-model-platform": ["Design", "Identifies credible abuse paths and maps them to verifiable controls.", "Threat-model invitations, bank imports, and shared transaction access.", "Assets, trust boundaries, threat scenarios, mitigations, verification plans, and residual risks.", "CTRL-AUTH-005 — an invited user cannot read household data until the invitation is accepted by the intended identity."],
  "plan-product-delivery": ["Plan", "Breaks the product into small vertical slices that can be demonstrated and verified.", "Plan delivery of the shared transaction review experience.", "Sequenced slices with dependencies, risks, acceptance evidence, and readiness gates.", "Slice 1 connects one real imported transaction from storage to mobile review, authorization, audit log, and an end-to-end test."],
  "execute-product-task": ["Deliver", "Completes one bounded task while preserving scope, evidence, and project context.", "Implement REQ-EXP-004 from the approved delivery plan.", "A focused change, updated tests and documentation, verification evidence, and explicitly recorded follow-ups.", "Completed audit history and restore action; budget analytics remains untouched and is recorded as out of scope."],
  "develop-with-tests": ["Deliver", "Uses the smallest meaningful tests to prove behavior through implementation.", "Add transaction-category undo using test-driven development.", "A failing behavior test, minimal implementation, passing regression suite, and concise refactoring evidence.", "The test proves undo restores both the category and audit history after an optimistic mobile update."],
  "build-web-feature": ["Deliver", "Connects interface, server, data, permissions, and tests into one real feature.", "Build the household invitation flow end to end.", "Working responsive UI, API behavior, persistence, authorization, validation, accessible states, and automated tests.", "An expired invitation shows a useful recovery path; cross-household acceptance is rejected on the server and covered by E2E tests."],
  "debug-platform": ["Deliver", "Investigates failures from evidence and root cause before changing code.", "Find why some imported transactions appear twice after a network retry.", "A reproducible case, evidence timeline, root cause, smallest safe fix, regression test, and remaining uncertainty.", "Root cause: the retry generated a new import key. Fix: derive a stable idempotency key from source account and transaction identity."],
  "review-product-change": ["Prove", "Checks specification alignment first, then implementation quality and risk.", "Review the household invitation pull request against the PRD.", "Prioritized findings with locations, impact, evidence, and concrete remediation—not a vague approval.", "HIGH — the UI hides expired invitations, but the API still accepts them because expiry is never enforced server-side."],
  "test-platform": ["Prove", "Tests complete journeys, roles, security boundaries, data integrity, and recovery.", "Test the release candidate across owner and member roles on mobile and desktop.", "Risk-based functional, E2E, authorization, privacy, migration, resilience, and accessibility evidence.", "Pass: owners can revoke access. Fail: a revoked session can read cached API data for five minutes. Release is blocked."],
  "verify-web-product": ["Prove", "Runs an independent readiness check using fresh, reproducible evidence.", "Verify the deployed preview against its release requirements.", "A requirement-by-requirement verdict, browser evidence, unresolved findings, and an honest release recommendation.", "CONDITIONAL GO — all core journeys pass, but keyboard focus after closing the mobile review sheet must be fixed."],
  "prepare-deployment": ["Launch", "Makes release, observation, rollback, and ownership explicit before production.", "Prepare version 1.2.0 for production deployment.", "A go/no-go assessment, migration plan, smoke checks, monitoring, abort thresholds, rollback steps, and owners.", "Abort if import error rate exceeds 2% for ten minutes; roll back the worker while preserving the backward-compatible schema."],
  "ship-web-product": ["Orchestrate", "Coordinates the appropriate skills from product uncertainty through verified delivery.", "Take this household-expense idea from analysis to a deployment-ready web product.", "A right-sized workflow, connected artifacts, decision gates, traceability, test evidence, and permission before production actions.", "The agent pauses at each material product decision and never treats generated screens or passing unit tests as proof of readiness."],
};

const skillDialog = document.querySelector("[data-skill-dialog]");
let skillOpener;

document.querySelectorAll("[data-skill]").forEach((button) => {
  button.addEventListener("click", () => {
    const name = button.dataset.skill;
    const example = skillExamples[name];
    if (!skillDialog || !example) return;
    skillOpener = button;
    const [stage, purpose, prompt, output, result] = example;
    skillDialog.querySelector("[data-skill-stage]").textContent = stage;
    skillDialog.querySelector("[data-skill-name]").textContent = name;
    skillDialog.querySelector("[data-skill-purpose]").textContent = purpose;
    skillDialog.querySelector("[data-skill-prompt]").textContent = `“${prompt}”`;
    skillDialog.querySelector("[data-skill-output]").textContent = output;
    skillDialog.querySelector("[data-skill-result]").textContent = result;
    if (typeof skillDialog.showModal === "function") {
      skillDialog.showModal();
    } else {
      skillDialog.setAttribute("open", "");
      skillDialog.classList.add("is-fallback-open");
    }
  });
});

function closeSkillDialog() {
  if (skillDialog?.open && typeof skillDialog.close === "function") {
    skillDialog.close();
  } else {
    skillDialog?.removeAttribute("open");
  }
  skillDialog?.classList.remove("is-fallback-open");
  skillOpener?.focus();
}

skillDialog?.querySelector("[data-skill-close]")?.addEventListener("click", closeSkillDialog);
skillDialog?.addEventListener("click", (event) => {
  if (event.target === skillDialog) closeSkillDialog();
});

document.querySelectorAll("[data-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    const original = button.textContent;
    try {
      await navigator.clipboard.writeText(button.dataset.copy);
      button.textContent = "Copied";
    } catch {
      button.textContent = "Select and copy the command";
    }
    window.setTimeout(() => { button.textContent = original; }, 1800);
  });
});
