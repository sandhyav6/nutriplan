import { PageHeader } from '../components/layout/PageHeader'
import { Card, CardTitle } from '../components/ui/Card'
import { useAuth } from '../hooks/useAuth'

const GETTING_STARTED = [
  ['Create an account', 'Register with your email address and a password (at least 8 characters with a letter and a number).'],
  ['Set up your profile', 'Enter your age, height, weight, activity level, dietary preference, allergies, health goal, weekly budget and the time you can spend cooking each meal.'],
  ['Check your nutrition profile', 'NutriPlan calculates your BMI and daily calorie and protein targets from your profile.'],
  ['Generate a weekly plan', 'Open Meal Plan and select “Generate weekly plan” to get breakfast, lunch, dinner and a snack for seven days.'],
  ['Shop with the grocery list', 'The grocery list combines every ingredient of the week into one list with estimated costs.'],
  ['Give feedback', 'Open a meal and mark it Favourite, Like, Skip or Dislike. Future plans use your feedback.'],
] as const

const FAQ = [
  {
    q: 'How are meals chosen?',
    a: 'A rule engine first removes every recipe that does not match your diet, contains a declared allergen or excluded food, or takes longer than your cooking time. The remaining recipes are ranked by how well they fit your calorie and protein targets, your budget and your past feedback, then arranged so no meal appears more than twice a week.',
  },
  {
    q: 'Why is a slot empty?',
    a: 'If no recipe satisfies all of your hard constraints for that slot, NutriPlan leaves it empty and explains why instead of recommending something unsafe. Allowing more cooking time or removing a restriction usually fills it.',
  },
  {
    q: 'What does “Replace meal” do?',
    a: 'It swaps one meal for another of the same category that fits the same diet and allergy rules, has similar calories (within 20%) and keeps your plan within your weekly budget. Your grocery list is updated automatically. If no alternative exists, your current meal is kept and you are told why.',
  },
  {
    q: 'How does feedback change my plans?',
    a: 'Each reaction has a weight: Favourite +3, Like +1, Skip −1, Dislike −3. Meals with a higher score are recommended more often and meals similar to your favourites get a boost. Changing your reaction to a meal replaces your earlier one.',
  },
  {
    q: 'Why do some meals show “1.5× serving”?',
    a: 'Recipes are stored as single servings. The planner adjusts portion sizes (between 0.75× and 2×) so your day adds up to your calorie target. Ingredient quantities and costs are scaled to match.',
  },
  {
    q: 'How is the grocery list calculated?',
    a: 'All ingredients from the week are added together – for example 200 g plus 300 g of rice becomes 500 g – duplicates are removed, and large amounts are shown in kg or litres. Costs are estimates for the exact quantities your meals use.',
  },
  {
    q: 'What if my budget is too low?',
    a: 'NutriPlan never goes over your weekly budget. If no safe plan fits, it tells you the lowest cost it could achieve so you can adjust your budget or other settings.',
  },
  {
    q: 'Where do the nutrition values and prices come from?',
    a: 'Release 1.0 ships with an illustrative development dataset: approximate public reference nutrition values and indicative Indian retail prices in ₹. It is not verified nutrition or price data. Administrators can correct or replace it in the admin panel.',
  },
  {
    q: 'Is this medical advice?',
    a: 'No. Nutrition values are estimates. If you have a medical condition or medical dietary restrictions, consult a doctor or registered dietitian.',
  },
] as const

const ADMIN_GUIDE = [
  ['Foods', 'Add each ingredient with its food group, diet type, canonical unit (g, ml or piece), price and allergens. A food’s unit cannot change while recipes use it.'],
  ['Nutrition values', 'Enter calories, protein, carbohydrates and fat per quantity of the food’s unit (for example per 100 g). Fibre, sugar, sodium and cholesterol are optional.'],
  ['Recipes', 'Choose one meal category, the preparation time and the ingredient quantities for one serving. Nutrition, cost, diet type and allergens are calculated automatically and recalculated whenever a food changes. Recipes used in plans cannot be deleted – mark them inactive instead.'],
  ['Categories', 'The four categories (breakfast, lunch, dinner, snack) are fixed. You can rename them and edit descriptions.'],
  ['Administrator accounts', 'Administrators are created on the server with `python -m app.cli create-admin` using the NUTRIPLAN_ADMIN_EMAIL and NUTRIPLAN_ADMIN_PASSWORD environment variables. Public registration can never create an administrator.'],
] as const

export function HelpPage() {
  const { state } = useAuth()
  const isAdmin = state.status === 'authenticated' && state.user.role === 'admin'

  return (
    <>
      <PageHeader
        eyebrow="Help"
        title="Help and frequently asked questions"
        description="How to get started with NutriPlan, and answers about meal plans, replacements, the grocery list and feedback."
      />
      <div className="space-y-6">
        <Card>
          <CardTitle>Getting started</CardTitle>
          <ol className="mt-4 space-y-3">
            {GETTING_STARTED.map(([title, text], i) => (
              <li key={title} className="flex gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-600 text-sm font-semibold text-white">
                  {i + 1}
                </span>
                <span>
                  <span className="block font-semibold text-ink">{title}</span>
                  <span className="text-sm text-ink-muted">{text}</span>
                </span>
              </li>
            ))}
          </ol>
        </Card>

        <Card>
          <CardTitle>Frequently asked questions</CardTitle>
          <div className="mt-3 divide-y divide-line">
            {FAQ.map((item) => (
              <details key={item.q} className="group py-3">
                <summary className="cursor-pointer list-none font-medium text-ink marker:hidden">
                  <span className="mr-2 inline-block text-brand-700 transition-transform group-open:rotate-90" aria-hidden="true">
                    ›
                  </span>
                  {item.q}
                </summary>
                <p className="mt-2 pl-5 text-sm leading-relaxed text-ink-muted">{item.a}</p>
              </details>
            ))}
          </div>
        </Card>

        {isAdmin && (
          <Card>
            <CardTitle>Administrator guide</CardTitle>
            <dl className="mt-4 space-y-4">
              {ADMIN_GUIDE.map(([title, text]) => (
                <div key={title}>
                  <dt className="font-semibold text-ink">{title}</dt>
                  <dd className="mt-1 text-sm leading-relaxed text-ink-muted">{text}</dd>
                </div>
              ))}
            </dl>
          </Card>
        )}
      </div>
    </>
  )
}
