# ADR-{NNN}: {Tytuł decyzji architektonicznej}

## Metadane

| Pole | Wartość |
|------|---------|
| **Status** | Proponowany / Zaakceptowany / Odrzucony / Przestarzały |
| **Data** | {YYYY-MM-DD} |
| **Autor** | {imię i nazwisko} |
| **Decydenci** | {lista osób podejmujących decyzję} |
| **Powiązane ADR** | [ADR-XXX](./ADR-XXX-nazwa.md) |
| **Powiązana funkcjonalność** | [Link do spec](../specs/{feature}/README.md) |

---

## Kontekst

### Problem
{Opisz problem lub potrzebę, która wymaga podjęcia decyzji architektonicznej.}

### Tło
{Podaj dodatkowy kontekst:
- Obecny stan systemu
- Ograniczenia techniczne
- Wymagania biznesowe
- Presja czasowa lub zasobowa}

### Wymagania
- {Wymaganie 1}
- {Wymaganie 2}
- {Wymaganie 3}

### Ograniczenia
- {Ograniczenie 1}
- {Ograniczenie 2}

---

## Rozważane opcje

### Opcja 1: {Nazwa opcji}

**Opis:**
{Szczegółowy opis rozwiązania}

**Zalety:**
- {Zaleta 1}
- {Zaleta 2}

**Wady:**
- {Wada 1}
- {Wada 2}

**Szacowany koszt implementacji:**
- Nakład pracy: {niski/średni/wysoki}
- Ryzyko: {niskie/średnie/wysokie}

---

### Opcja 2: {Nazwa opcji}

**Opis:**
{Szczegółowy opis rozwiązania}

**Zalety:**
- {Zaleta 1}
- {Zaleta 2}

**Wady:**
- {Wada 1}
- {Wada 2}

**Szacowany koszt implementacji:**
- Nakład pracy: {niski/średni/wysoki}
- Ryzyko: {niskie/średnie/wysokie}

---

### Opcja 3: {Nazwa opcji} (opcjonalnie)

**Opis:**
{Szczegółowy opis rozwiązania}

**Zalety:**
- {Zaleta 1}
- {Zaleta 2}

**Wady:**
- {Wada 1}
- {Wada 2}

---

## Porównanie opcji

| Kryterium | Opcja 1 | Opcja 2 | Opcja 3 |
|-----------|---------|---------|---------|
| Złożoność implementacji | {+/-} | {+/-} | {+/-} |
| Skalowalność | {+/-} | {+/-} | {+/-} |
| Wydajność | {+/-} | {+/-} | {+/-} |
| Łatwość utrzymania | {+/-} | {+/-} | {+/-} |
| Zgodność z istniejącą architekturą | {+/-} | {+/-} | {+/-} |
| Koszt | {+/-} | {+/-} | {+/-} |

**Legenda:** + (korzystne), - (niekorzystne), 0 (neutralne)

---

## Decyzja

**Wybrana opcja:** Opcja {X} - {Nazwa}

### Uzasadnienie
{Wyjaśnij dlaczego ta opcja została wybrana:
- Które zalety były decydujące?
- Jak radzisz sobie z wadami?
- Jakie czynniki przesądziły o wyborze?}

---

## Konsekwencje

### Pozytywne
- {Pozytywna konsekwencja 1}
- {Pozytywna konsekwencja 2}

### Negatywne
- {Negatywna konsekwencja 1}
- {Negatywna konsekwencja 2}

### Neutralne
- {Neutralna konsekwencja}

---

## Plan implementacji

### Kroki
1. {Krok 1}
2. {Krok 2}
3. {Krok 3}

### Zmiany w kodzie
- `{ścieżka/do/pliku1}` - {opis zmiany}
- `{ścieżka/do/pliku2}` - {opis zmiany}

### Migracja danych
{Opis migracji jeśli wymagana, lub "Nie dotyczy"}

### Testy
- [ ] Testy jednostkowe
- [ ] Testy integracyjne
- [ ] Testy wydajnościowe

---

## Ryzyka i ich mitygacja

| Ryzyko | Prawdopodobieństwo | Wpływ | Mitygacja |
|--------|-------------------|-------|-----------|
| {Ryzyko 1} | Niskie/Średnie/Wysokie | Niski/Średni/Wysoki | {Sposób mitygacji} |
| {Ryzyko 2} | Niskie/Średnie/Wysokie | Niski/Średni/Wysoki | {Sposób mitygacji} |

---

## Alternatywy odrzucone

### {Nazwa odrzuconej alternatywy}
**Powód odrzucenia:** {Dlaczego ta opcja została odrzucona}

---

## Powiązane dokumenty

- [Specyfikacja funkcjonalna](../specs/{feature}/README.md)
- [Specyfikacja techniczna](../specs/{feature}/TECHNICAL.md)
- [ADR-{XXX}](./ADR-XXX-nazwa.md) - powiązana decyzja

---

## Notatki

{Dodatkowe notatki, uwagi, lub informacje, które mogą być przydatne w przyszłości}

---

## Historia zmian

| Wersja | Data | Autor | Opis zmian |
|--------|------|-------|------------|
| 1.0 | {data} | {autor} | Wersja początkowa |
| 1.1 | {data} | {autor} | {Opis zmian} |

---

## Przegląd i aktualizacja

**Data ostatniego przeglądu:** {YYYY-MM-DD}
**Następny przegląd:** {YYYY-MM-DD}

Ta decyzja powinna być przeglądana:
- [ ] Przy znaczących zmianach w architekturze
- [ ] Przy aktualizacji zależności
- [ ] Co {X} miesięcy
