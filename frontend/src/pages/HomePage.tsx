import { ButtonLink } from '../components/ui/Button'
import { Card, CardDescription, CardTitle } from '../components/ui/Card'
import { ApiStatusIndicator } from '../features/health/ApiStatusIndicator'

const FLOW = [
  'Register',
  'Create profile',
  'Nutrition profile',
  'Weekly meal plan',
  'Grocery list',
  'Feedback',
] as const

const FEATURES = [
  {
    title: 'Personal nutrition targets',
    text: 'Your age, body stats, activity level and goal become a concrete calorie and protein target before any meal is chosen.',
  },
  {
    title: 'Rule-based weekly plans',
    text: 'Breakfast, lunch, dinner and a snack for 7 days – filtered by diet, allergies, budget and cooking time.',
  },
  {
    title: 'One consolidated grocery list',
    text: 'Ingredients from the whole week are combined and de-duplicated, with estimated cost in ₹.',
  },
  {
    title: 'Learns from your feedback',
    text: 'Like, dislike, skip or favourite meals. Future plans give more weight to what you enjoy.',
  },
  {
    title: 'Swap a single meal',
    text: 'Replace one meal without breaking your budget, calorie target or diet type.',
  },
  {
    title: 'Safety first',
    text: 'Declared allergens and dietary restrictions are hard rules – they are never traded for variety or ranking.',
  },
] as const

export function HomePage() {
  return (
    <div className="space-y-14">
      <section className="grid items-center gap-10 pt-2 lg:grid-cols-[1.2fr_1fr]">
        <div>
          <p className="text-sm font-semibold tracking-wider text-brand-700 uppercase">
            Adaptive meal planning based on lifestyle
          </p>
          <h1 className="mt-3 text-4xl font-bold tracking-tight text-ink sm:text-5xl">
            Healthy weekly meals that fit your budget and your schedule.
          </h1>
          <p className="mt-4 max-w-xl text-lg leading-relaxed text-ink-muted">
            NutriPlan builds a personalised 7-day meal plan and grocery list from your dietary
            preferences, health goal, weekly budget and available cooking time – for students,
            working professionals, families and fitness enthusiasts.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <ButtonLink to="/register" size="lg">
              Create an account
            </ButtonLink>
            <ButtonLink to="/meal-plan" variant="secondary" size="lg">
              See the meal plan layout
            </ButtonLink>
          </div>
        </div>

        <Card className="bg-brand-50/60">
          <CardTitle>How NutriPlan works</CardTitle>
          <ol className="mt-4 space-y-3">
            {FLOW.map((step, index) => (
              <li key={step} className="flex items-center gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-600 text-sm font-semibold text-white">
                  {index + 1}
                </span>
                <span className="font-medium text-ink">{step}</span>
              </li>
            ))}
          </ol>
          <p className="mt-4 text-sm text-ink-muted">
            Feedback improves future recommendations, closing the loop.
          </p>
        </Card>
      </section>

      <section aria-labelledby="features-heading">
        <h2 id="features-heading" className="text-2xl font-bold tracking-tight text-ink">
          What NutriPlan will do for you
        </h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <Card key={feature.title}>
              <CardTitle className="text-base">{feature.title}</CardTitle>
              <CardDescription>{feature.text}</CardDescription>
            </Card>
          ))}
        </div>
      </section>

      <section aria-labelledby="status-heading">
        <Card>
          <h2 id="status-heading" className="text-lg font-semibold text-ink">
            Project status
          </h2>
          <p className="mt-1 text-sm leading-relaxed text-ink-muted">
            This build is the Milestone 0 project foundation. Screens show their final layout, and
            each one states which milestone will make it functional. The indicator below calls the
            real backend health endpoint.
          </p>
          <div className="mt-4">
            <ApiStatusIndicator pollMs={0} />
          </div>
        </Card>
      </section>
    </div>
  )
}
