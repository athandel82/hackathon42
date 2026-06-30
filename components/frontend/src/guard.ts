// Input guard — a simple, in-app pre-check run before /analyze. It mirrors the
// kinds of policies an Amazon Bedrock Guardrail enforces (prompt-injection /
// jailbreak detection, denied topics/profanity, and a relevance gate) so the UI
// can reject obviously invalid requests fast and explain why.
//
// Kept deliberately lightweight and local (no extra endpoint). In production the
// same contract (GuardResult) would be produced by a Bedrock Guardrail.

import type { GuardResult } from './api/types';

const MIN_LENGTH = 8;

// Prompt-injection / jailbreak signatures.
const INJECTION_PATTERNS: RegExp[] = [
  /ignore\s+(all\s+)?(previous|prior|above)\s+instructions/i,
  /system\s+prompt/i,
  /jailbreak/i,
  /you\s+are\s+now\b/i,
  /disregard\s+(the\s+)?(rules|guardrails)/i,
];

// Mild profanity / abuse denylist (illustrative, not exhaustive).
const PROFANITY = /\b(fuck|shit|bitch|asshole)\b/i;

// Relevance gate: a valid request should describe an automotive architecture
// change. Require at least one action verb AND one domain noun, or an explicit
// analysis verb.
const ACTION_VERBS =
  /\b(remove|delete|add|introduce|change|modify|replace|swap|rename|reroute|move|merge|split|migrate|analyze|analyse|assess|evaluate|impact)\b/i;
const DOMAIN_NOUNS =
  /\b(ecu|component|composition|signal|pdu|frame|bus|can|lin|flexray|ethernet|module|door|window|gateway|controller|sensor|actuator|harness|network|node|software|swc|port|interface|dtc|diagnostic)\b/i;

export function evaluateInputGuard(rawRequest: string): GuardResult {
  const text = rawRequest.trim();

  if (text.length === 0) {
    return { allowed: false, reason: 'Please enter a change request.', categories: ['empty'] };
  }

  if (text.length < MIN_LENGTH) {
    return {
      allowed: false,
      reason: 'The request is too short to analyze. Describe the change in a sentence.',
      categories: ['too_vague'],
    };
  }

  if (INJECTION_PATTERNS.some((re) => re.test(text))) {
    return {
      allowed: false,
      reason: 'This request looks like a prompt-injection attempt and was blocked.',
      categories: ['prompt_injection'],
    };
  }

  if (PROFANITY.test(text)) {
    return {
      allowed: false,
      reason: 'Please rephrase without offensive language.',
      categories: ['profanity'],
    };
  }

  const hasAction = ACTION_VERBS.test(text);
  const hasDomain = DOMAIN_NOUNS.test(text);
  if (!hasAction || !hasDomain) {
    return {
      allowed: false,
      reason:
        'This does not look like a vehicle-architecture change request. Try e.g. "remove the Door component" or "reroute the window-position signal".',
      categories: ['off_topic'],
    };
  }

  return { allowed: true };
}
