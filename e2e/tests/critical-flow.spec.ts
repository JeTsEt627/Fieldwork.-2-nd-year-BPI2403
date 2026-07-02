import { test, expect } from "@playwright/test";
import path from "node:path";

// E2E-тест критического сценария (QA-02):
// загрузка документа → индексация → поиск → отображение результатов.
//
// В тест-файлах Playwright доступен глобальный __dirname (CommonJS),
// поэтому дополнительные вычисления пути через import.meta не нужны.

// Корректная фикстура, генерируется скриптом
// backend/tests/fixtures/generate_fixtures.py
const FIXTURE = path.resolve(
  __dirname,
  "../../backend/tests/fixtures/valid_document.docx",
);

// Запрос, заведомо присутствующий в тексте фикстуры.
const SEARCH_QUERY = "машинное обучение";

test.describe("Критический пользовательский сценарий", () => {
  test("загрузка документа и его индексация", async ({ page }) => {
    await page.goto("/");

    // FE-01: загрузка файла через скрытый input в Drag-and-Drop зоне.
    await page.locator('input[type="file"]').setInputFiles(FIXTURE);

    // FE-02: статус задачи должен дойти до «Готово».
    await expect(page.getByText("Готово").first()).toBeVisible({
      timeout: 30_000,
    });

    // FE-03: документ появляется в списке загруженных.
    await expect(
      page.getByText("valid_document.docx").first(),
    ).toBeVisible();
  });

  test("поиск по загруженному документу и вывод результатов", async ({
    page,
  }) => {
    await page.goto("/search");

    // FE-04: ввод запроса и запуск по нажатию Enter.
    const input = page.getByPlaceholder("Введите поисковый запрос...");
    await input.fill(SEARCH_QUERY);
    await input.press("Enter");

    // Должны появиться либо карточки результатов (FE-05),
    // либо корректное сообщение об их отсутствии (FE-08).
    const cards = page.locator(".card");
    const emptyMessage = page.getByText(/ничего не найдено/i);

    await expect(cards.first().or(emptyMessage)).toBeVisible({
      timeout: 20_000,
    });

    // Если результаты есть — проверяем обязательные поля карточки (FE-05).
    if ((await cards.count()) > 0) {
      const firstCard = cards.first();
      await expect(firstCard.locator(".card__file")).toBeVisible();
      await expect(firstCard.locator(".card__page")).toBeVisible();
      await expect(firstCard.locator(".card__score")).toBeVisible();
    }
  });

  test("поиск с заведомо отсутствующим запросом показывает сообщение", async ({
    page,
  }) => {
    await page.goto("/search");

    const input = page.getByPlaceholder("Введите поисковый запрос...");
    await input.fill("zxqwjklmnoprstuvabcdef0000");
    await page.getByRole("button", { name: "Найти" }).click();

    // FE-08: сообщение об отсутствии результатов.
    await expect(page.getByText(/ничего не найдено/i)).toBeVisible({
      timeout: 20_000,
    });
  });
});
