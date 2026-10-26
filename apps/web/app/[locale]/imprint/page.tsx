import Link from "next/link";
import { marked } from "marked";
import { Content } from "@/modules/learning/content";
export default function Page() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-16">
      <Link href="/">← Databrix</Link>
      <div className="mt-10">
        <Content
          html={marked.parse(
            "# Impressum\n\nDie folgende Website ist das Ergebnis des Databrix-Forschungsprojekts, welches innerhalb des Studiengangs Wirtschaftsingenieurwesen, DHBW Stuttgart, in Kooperation mit der Firma Votan Enterprise und gefördert durch InvestBW stattfindet. Mehr zum Forschungsprojekt sowie dem Forschungsträger erfahren Sie auf folgender Projektseite: [https://www.dhbw-stuttgart.de/forschung-transfer/technik/projekte/databrix/](https://www.dhbw-stuttgart.de/forschung-transfer/technik/projekte/databrix/)\n\n## Angaben gemäß § 5 TMG\n\nVotan Enterprise UG (haftungsbeschraenkt)\nFranziskaweg 1\n70599 Stuttgart\n\n## Kontakt\n\nE-Mail: info@databrix.org\n",
            { async: false },
          )}
        />
      </div>
    </main>
  );
}
