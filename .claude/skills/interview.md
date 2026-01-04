# Interview Skill

This skill conducts structured requirements clarification interviews using the AskUserQuestion tool. It is **MANDATORY** for all agents before entering plan mode or making implementation decisions when requirements are unclear.

## CRITICAL: When to Use This Skill

**ALL agents MUST invoke `/interview` when:**

1. **Vague Requirements** - User request lacks specific details
2. **Multiple Valid Approaches** - More than one reasonable implementation path exists
3. **Technical Decisions** - Architecture, library, or pattern choices needed
4. **Functional Ambiguity** - Business logic or user flow unclear
5. **A/B Decision Points** - Trade-offs between options need user input
6. **Specification Creation** - Before writing any spec document
7. **Before Plan Mode** - Always clarify before planning implementation

**NEVER assume. ALWAYS ask using structured questions.**

---

## Interview Protocol

### Rule 1: Use AskUserQuestion for EVERY Question

Every clarification MUST use the `AskUserQuestion` tool with:
- 2-4 clear, distinct options
- Brief descriptions explaining each option
- Appropriate `multiSelect` setting (true for checkboxes, false for radio)
- User can always select "Other" for custom input

### Rule 2: One Question at a Time

Ask questions sequentially, adapting based on answers. Skip irrelevant questions.

### Rule 3: Summarize Before Proceeding

After gathering answers, present a clear summary for confirmation before moving to planning or implementation.

---

## Question Categories by Agent Type

### For All Agents (General Clarification)

**Scope & Priority:**
```
Question: "Jaki jest zakres tej zmiany?"
Header: "Zakres"
Options:
  - label: "Mała (1-2 pliki)"
    description: "Drobna zmiana w istniejącym kodzie"
  - label: "Średnia (3-5 plików)"
    description: "Nowa funkcjonalność lub większa modyfikacja"
  - label: "Duża (6+ plików)"
    description: "Znacząca zmiana architekturalna"
  - label: "Nie wiem jeszcze"
    description: "Wymaga dalszej analizy"
multiSelect: false
```

**Priority:**
```
Question: "Jaki jest priorytet tej zmiany?"
Header: "Priorytet"
Options:
  - label: "Krytyczny"
    description: "Blokuje inne prace lub produkcję"
  - label: "Wysoki"
    description: "Potrzebne wkrótce"
  - label: "Średni"
    description: "Zaplanowane do realizacji"
  - label: "Niski"
    description: "Miło mieć, nie pilne"
multiSelect: false
```

### For requirements-analyst Agent

**Feature Type:**
```
Question: "Jakiego typu jest ta funkcjonalność?"
Header: "Typ"
Options:
  - label: "Nowa funkcjonalność"
    description: "Zupełnie nowa możliwość w systemie"
  - label: "Rozszerzenie istniejącej"
    description: "Dodanie do już działającej funkcji"
  - label: "Naprawa błędu"
    description: "Korekta nieprawidłowego działania"
  - label: "Refaktoryzacja"
    description: "Poprawa kodu bez zmiany zachowania"
multiSelect: false
```

**User Personas:**
```
Question: "Kto będzie używał tej funkcjonalności?"
Header: "Użytkownicy"
Options:
  - label: "Właściciel/Manager"
    description: "Osoba zarządzająca lokalem"
  - label: "Pracownik"
    description: "Osoba obsługująca klientów"
  - label: "System automatyczny"
    description: "Zadania wykonywane automatycznie"
  - label: "Wielu użytkowników"
    description: "Różne role z różnym dostępem"
multiSelect: true
```

**Success Criteria:**
```
Question: "Jak poznamy, że funkcjonalność działa poprawnie?"
Header: "Kryteria"
Options:
  - label: "Konkretny wynik/output"
    description: "System zwraca określone dane"
  - label: "Zmiana stanu"
    description: "Dane w systemie się zmieniają"
  - label: "Powiadomienie użytkownika"
    description: "Użytkownik otrzymuje informację zwrotną"
  - label: "Metryka wydajności"
    description: "Mierzalna poprawa (czas, ilość, etc.)"
multiSelect: true
```

### For database-architect Agent

**Schema Changes:**
```
Question: "Jakie zmiany w bazie danych są potrzebne?"
Header: "Schemat"
Options:
  - label: "Nowa tabela"
    description: "Utworzenie nowej encji"
  - label: "Modyfikacja istniejącej"
    description: "Dodanie/zmiana kolumn"
  - label: "Nowe relacje"
    description: "Połączenia między tabelami"
  - label: "Brak zmian"
    description: "Obecny schemat wystarcza"
multiSelect: true
```

**Data Migration:**
```
Question: "Czy istniejące dane wymagają migracji?"
Header: "Migracja"
Options:
  - label: "Tak, z transformacją"
    description: "Dane muszą być przekształcone"
  - label: "Tak, proste przeniesienie"
    description: "Dane tylko przemieszczone"
  - label: "Nie, nowe dane"
    description: "Funkcja dotyczy tylko nowych rekordów"
  - label: "Do ustalenia"
    description: "Wymaga analizy istniejących danych"
multiSelect: false
```

### For fastapi-backend-architect Agent

**API Design:**
```
Question: "Jakie endpointy API są potrzebne?"
Header: "API"
Options:
  - label: "CRUD (Create/Read/Update/Delete)"
    description: "Pełny zestaw operacji na zasobie"
  - label: "Tylko odczyt"
    description: "GET endpoints"
  - label: "Akcja/Operacja"
    description: "POST endpoint wykonujący akcję"
  - label: "Integracja zewnętrzna"
    description: "Połączenie z zewnętrznym API"
multiSelect: true
```

**Authentication:**
```
Question: "Jakie wymagania autoryzacyjne?"
Header: "Autoryzacja"
Options:
  - label: "Publiczny endpoint"
    description: "Dostępny bez logowania"
  - label: "Zalogowany użytkownik"
    description: "Wymaga aktywnej sesji"
  - label: "Określona rola"
    description: "Tylko dla admin/manager/etc."
  - label: "Właściciel zasobu"
    description: "Tylko dla twórcy/właściciela danych"
multiSelect: false
```

### For react-frontend-architect Agent

**UI Components:**
```
Question: "Jakie komponenty UI są potrzebne?"
Header: "Komponenty"
Options:
  - label: "Nowa strona"
    description: "Całkowicie nowy widok"
  - label: "Modal/Dialog"
    description: "Okno modalne"
  - label: "Formularz"
    description: "Wprowadzanie danych"
  - label: "Lista/Tabela"
    description: "Wyświetlanie wielu elementów"
multiSelect: true
```

**State Management:**
```
Question: "Jak zarządzać stanem dla tej funkcji?"
Header: "Stan"
Options:
  - label: "Lokalny (useState)"
    description: "Stan tylko w komponencie"
  - label: "Context"
    description: "Stan współdzielony między komponentami"
  - label: "React Query"
    description: "Stan serwerowy z cache"
  - label: "Do ustalenia"
    description: "Wymaga analizy wymagań"
multiSelect: false
```

### For testing-engineer Agent

**Test Scope:**
```
Question: "Jaki zakres testów jest potrzebny?"
Header: "Testy"
Options:
  - label: "Unit testy"
    description: "Izolowane testy funkcji/komponentów"
  - label: "Integration testy"
    description: "Testy współpracy modułów"
  - label: "E2E testy"
    description: "Testy całego flow użytkownika"
  - label: "Wszystkie poziomy"
    description: "Pełna piramida testów"
multiSelect: true
```

**Test Data:**
```
Question: "Jakie dane testowe są potrzebne?"
Header: "Dane"
Options:
  - label: "Nowe buildery"
    description: "Nowe fabryki danych testowych"
  - label: "Istniejące buildery"
    description: "Użycie obecnych fabryk"
  - label: "Fixtures z plików"
    description: "Dane z JSON/CSV"
  - label: "Property-based"
    description: "Generowane przez Hypothesis"
multiSelect: true
```

### For deployment-engineer Agent

**Deployment Target:**
```
Question: "Gdzie deployować tę zmianę?"
Header: "Środowisko"
Options:
  - label: "Tylko lokalne Docker"
    description: "Testowanie lokalne"
  - label: "VPS staging"
    description: "Środowisko testowe na serwerze"
  - label: "VPS produkcja"
    description: "Środowisko produkcyjne"
  - label: "Wszystkie środowiska"
    description: "Pełny pipeline CI/CD"
multiSelect: true
```

---

## A/B Decision Template

When multiple valid approaches exist:

```
Question: "Który z podejść preferujesz dla [konkretny problem]?"
Header: "Podejście"
Options:
  - label: "Opcja A: [nazwa]"
    description: "[Zalety i wady opcji A]"
  - label: "Opcja B: [nazwa]"
    description: "[Zalety i wady opcji B]"
  - label: "Opcja C: [nazwa]" (opcjonalnie)
    description: "[Zalety i wady opcji C]"
  - label: "Potrzebuję więcej informacji"
    description: "Wyjaśnij szczegóły każdej opcji"
multiSelect: false
```

---

## Trade-off Questions

When implementation involves trade-offs:

```
Question: "Co jest najważniejsze dla tej funkcjonalności?"
Header: "Priorytet"
Options:
  - label: "Szybkość implementacji"
    description: "Jak najszybciej działające rozwiązanie"
  - label: "Wydajność"
    description: "Optymalne działanie pod obciążeniem"
  - label: "Łatwość utrzymania"
    description: "Czysty kod, łatwe przyszłe zmiany"
  - label: "Doświadczenie użytkownika"
    description: "Najlepsza ergonomia i UX"
multiSelect: false
```

---

## Interview Output Format

After completing the interview, summarize:

```markdown
## Podsumowanie wywiadu

### Ustalenia:
- **Zakres**: [odpowiedź]
- **Priorytet**: [odpowiedź]
- **Typ**: [odpowiedź]
- [inne kluczowe ustalenia]

### Decyzje techniczne:
- [decyzja 1]
- [decyzja 2]

### Zidentyfikowane ryzyka:
- [ryzyko 1, jeśli jakieś]

### Następne kroki:
1. [krok 1]
2. [krok 2]

Czy powyższe podsumowanie jest poprawne? Jeśli tak, przechodzę do [planowania/implementacji].
```

---

## Language

Conduct the interview in Polish (the project's primary language) unless the user explicitly uses English.
