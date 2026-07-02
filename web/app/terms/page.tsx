import { getAllTerms } from "@/lib/terms";
import TermsBrowser from "./TermsBrowser";

export const dynamic = "force-static";

export default async function Page() {
  const terms = await getAllTerms();

  const grouped = {
    1: terms.filter((t) => t.tier === 1),
    2: terms.filter((t) => t.tier === 2),
    3: terms.filter((t) => t.tier === 3),
  };

  return (
    <div className="p-4 lg:p-8">
      <TermsBrowser grouped={grouped} />
    </div>
  );
}
