import { FarmsProof } from "@/components/farms-proof"

export default function Home() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-12">
      <div className="mb-10">
        <h1 className="text-3xl font-bold tracking-tight">cultivOS</h1>
        <p className="mt-2 text-muted-foreground">
          Inteligencia agricola de precision para Jalisco y Ontario.
        </p>
      </div>
      <section>
        <h2 className="mb-4 text-lg font-semibold">Granjas</h2>
        <FarmsProof />
      </section>
    </main>
  )
}
