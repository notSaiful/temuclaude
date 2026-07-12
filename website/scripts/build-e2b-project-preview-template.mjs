import { Template } from 'e2b';
import { PROJECT_PREVIEW_TEMPLATE, createProjectPreviewTemplate } from '../e2b/project-preview-template.mjs';

const apiKey = process.env.E2B_API_KEY?.trim();
if (!apiKey) {
  console.error('E2B_API_KEY is required to build the project preview template.');
  process.exit(2);
}

if (await Template.exists(PROJECT_PREVIEW_TEMPLATE, { apiKey })) {
  console.log(JSON.stringify({ template: PROJECT_PREVIEW_TEMPLATE, status: 'already-exists' }));
} else {
  const result = await Template.build(createProjectPreviewTemplate(), PROJECT_PREVIEW_TEMPLATE, {
    apiKey,
    cpuCount: 1,
    memoryMB: 1024,
    tags: ['v1', 'production'],
  });
  console.log(JSON.stringify({ template: result.name, status: 'ready', templateId: result.templateId }));
}
