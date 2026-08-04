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
