// Verified using the local-hotline connector on 2026-10-22. U.S. demo region.
// Static content: no API, provider, or classifier is required to render this.
export const support = {
  name: '988 Suicide & Crisis Lifeline',
  region: 'United States and its territories',
  description: 'Phone, text, and online chat are available for suicidal crisis or emotional distress.',
  links: [
    { text: 'Call 988', href: 'tel:988?oai_link_source=model_response_hotline' },
    { text: 'Text 988', href: 'sms:988?oai_link_source=model_response_hotline' },
    { text: 'Online chat', href: 'https://988lifeline.org/chat/?oai_link_source=model_response_hotline' },
    { text: '988 Lifeline website', href: 'https://988lifeline.org?oai_link_source=model_response_hotline' },
  ],
}
