import { notFound } from "next/navigation";
import { getAllTerms, getTerm } from "@/lib/terms";
import Term from "@/components/Term";

export const dynamic = "force-static";

export async function generateStaticParams() {
  const terms = await getAllTerms();

  return terms.map((term) => ({
    termId: term.id,
  }));
}

export default async function Page({
  params,
}: {
  params: Promise<{ termId: string }>;
}) {
  const { termId } = await params;

  const term = await getTerm(termId);

  if (!term) {  
    notFound();
  }

  return <Term term={term} />;
}