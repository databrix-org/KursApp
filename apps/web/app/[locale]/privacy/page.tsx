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
            "# Datenschutzerklärung\n\nDiese Datenschutzerklärung beschreibt, wie wir Ihre personenbezogenen Daten erfassen, verwenden und schützen, wenn Sie unsere Dienste nutzen.\n\n## 1. Verantwortliche Stelle\n\nDie verantwortliche Stelle für die Datenverarbeitung auf dieser Website ist:\n\nVotan Enterprise UG (haftungsbeschraenkt)\nFranziskaweg 1\n70599 Stuttgart\n\nE-Mail: info@databrix.org\n\n## 2. Erhebung und Speicherung personenbezogener Daten\n\nWir erfassen und speichern personenbezogene Daten nur, wenn Sie uns diese freiwillig zur Verfügung stellen, beispielsweise durch die Nutzung unserer Website, das Ausfüllen von Formularen oder die Kontaktaufnahme mit uns.\n\nDie erhobenen Daten können unter anderem Folgendes umfassen:\n\n- Name, E-Mail-Adresse, Telefonnummer\n- Zahlungsinformationen\n- IP-Adresse, Browsertyp, Betriebssystem\n- Nutzungsverhalten unserer Website\n\n## 3. Zweck der Datenverarbeitung\n\nWir verwenden Ihre personenbezogenen Daten zu folgenden Zwecken:\n\n- Zur Bereitstellung und Verbesserung unserer Dienstleistungen\n- Zur Bearbeitung Ihrer Anfragen\n- Zur Zahlungsabwicklung\n- Zur Einhaltung gesetzlicher Verpflichtungen\n\n## 4. Rechtsgrundlage für die Verarbeitung\n\nDie Verarbeitung Ihrer personenbezogenen Daten erfolgt auf der Grundlage folgender rechtlicher Bestimmungen:\n\n- Erlaubnis zur Erfüllung eines Vertrags (Art. 6 Abs. 1 lit. b DSGVO)\n- Berechtigtes Interesse (Art. 6 Abs. 1 lit. f DSGVO)\n- Gesetzliche Verpflichtung (Art. 6 Abs. 1 lit. c DSGVO)\n\n## 5. Weitergabe von Daten an Dritte\n\nWir geben Ihre Daten nur an Dritte weiter, wenn dies zur Vertragserfüllung notwendig ist, eine gesetzliche Verpflichtung besteht oder Sie uns Ihre ausdrückliche Einwilligung erteilt haben.\n\n## 6. Speicherdauer\n\nIhre personenbezogenen Daten werden nur so lange gespeichert, wie es zur Erfüllung der oben genannten Zwecke erforderlich ist oder gesetzliche Aufbewahrungspflichten bestehen.\n\n## 7. Ihre Rechte\n\nSie haben folgende Rechte hinsichtlich Ihrer personenbezogenen Daten:\n\n- Recht auf Auskunft (Art. 15 DSGVO)\n- Recht auf Berichtigung (Art. 16 DSGVO)\n- Recht auf Löschung (Art. 17 DSGVO)\n- Recht auf Einschränkung der Verarbeitung (Art. 18 DSGVO)\n- Recht auf Datenübertragbarkeit (Art. 20 DSGVO)\n- Recht auf Widerspruch gegen die Verarbeitung (Art. 21 DSGVO)\n\nZur Ausübung dieser Rechte können Sie uns jederzeit kontaktieren.\n\n## 8. Cookies und Tracking-Technologien\n\nUnsere Website verwendet Cookies und ähnliche Technologien, um die Benutzererfahrung zu verbessern. Sie können der Nutzung von Cookies jederzeit widersprechen oder diese in Ihren Browsereinstellungen deaktivieren.\n\n## 9. Datensicherheit\n\nWir setzen geeignete technische und organisatorische Maßnahmen ein, um Ihre Daten vor Verlust, Missbrauch oder unbefugtem Zugriff zu schützen.\n\n## 10. Änderungen der Datenschutzerklärung\n\nWir behalten uns vor, diese Datenschutzerklärung anzupassen, um gesetzlichen Anforderungen zu entsprechen oder Änderungen unserer Dienstleistungen zu berücksichtigen. Die aktuelle Version ist stets auf unserer Website einsehbar.\n",
            { async: false },
          )}
        />
      </div>
    </main>
  );
}
