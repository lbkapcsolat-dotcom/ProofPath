export function semanticExitCode(status) {
  const value = String(status ?? '');
  if (value.startsWith('PASS_')) return 0;
  if (value.startsWith('HOLD_')) return 2;
  if (value.startsWith('FAIL_')) return 1;
  return 1;
}

export function emitReceiptAndExit(receipt, statusField = 'status') {
  console.log(JSON.stringify(receipt));
  process.exit(semanticExitCode(receipt?.[statusField]));
}
