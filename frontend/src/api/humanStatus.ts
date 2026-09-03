// Maps status codes to sentences a farmer can act on. The UI never renders
// "500" or "Network request failed" (IMPLEMENTATION_REACT.md section 9).
export function humanStatus(status: number): string {
  switch (status) {
    case 401:
      return "Your session ended. Sign in again — nothing you entered has been lost.";
    case 403:
      return "You do not have access to this. If that is wrong, ask your district officer.";
    case 404:
      return "We could not find that.";
    case 409:
      return "That changed while you were working on it. Refresh to see the latest.";
    default:
      return status >= 500
        ? "We could not save that. It is stored on this phone and will be sent when the network returns."
        : "Something went wrong. Please try again.";
  }
}
