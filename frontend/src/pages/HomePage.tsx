// Главная страница: загрузка документов (FE-01, FE-02) и список загруженных
// документов (FE-03).

import { useState } from "react";

import { DocumentList } from "../components/DocumentList";
import { UploadZone } from "../components/UploadZone";

export function HomePage() {
  // Счётчик-триггер: увеличивается после каждой загрузки, чтобы список
  // документов перечитался с сервера.
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="page">
      <section className="panel">
        <h2>Загрузка документов</h2>
        <UploadZone onUploaded={() => setRefreshKey((k) => k + 1)} />
      </section>

      <DocumentList refreshKey={refreshKey} />
    </div>
  );
}
