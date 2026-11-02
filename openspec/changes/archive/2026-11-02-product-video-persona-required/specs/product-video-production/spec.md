## ADDED Requirements

### Requirement: Every product video has a persona

Creating a product video SHALL require a persona, and the persona SHALL be changeable later from the work's first step. A product video without a persona SHALL show a prompt to choose one, and its brief, voiceover and image generation SHALL be refused with a message that no persona is chosen. Changing the persona SHALL NOT alter already generated 导演稿, images or voice, and the page SHALL say the 导演稿 needs rewriting to speak as the new persona.

#### Scenario: Old product video without a persona
- **WHEN** the user opens product video 92, which has no persona
- **THEN** step 1 asks to choose a persona, and the editor's brief request is refused until one is chosen

### Requirement: Product video content follows the persona

A product video's brief SHALL carry the persona's profile, speech samples, brand rules, voice and portrait. Structure SHALL follow the product script style and hook, while wording, tone, catchphrases and how viewers are addressed — including the publish copy — SHALL follow the persona's profile and speech samples. The persona's own writing-method skill SHALL NOT be applied to product videos.

#### Scenario: Persona with speech samples
- **WHEN** a product video belongs to a persona with a speech-sample folder
- **THEN** the brief includes those samples and the rule to write the lines in the persona's way of speaking
