"""
Integration tests for API views.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from core.models import (
    Project, Document, Section, SectionContent, 
    Comment, Snapshot, Template
)


class HealthCheckTest(TestCase):
    def test_health_endpoint(self):
        client = Client()
        response = client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))


class ProjectsAPITest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_list_projects_empty(self):
        response = self.client.get('/api/projects')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_create_project(self):
        response = self.client.post(
            '/api/projects',
            data=json.dumps({'name': 'Test Project', 'description': 'A test'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['name'], 'Test Project')
        self.assertIn('id', data)

    def test_list_projects(self):
        Project.objects.create(name='Project 1')
        Project.objects.create(name='Project 2')
        
        response = self.client.get('/api/projects')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)


class DocumentsAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(name='Test Project')

    def test_get_document_detail(self):
        doc = Document.objects.create(
            project=self.project,
            title='Test Doc'
        )
        response = self.client.get(f'/api/documents/{doc.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], 'Test Doc')

    def test_document_not_found(self):
        response = self.client.get('/api/documents/00000000-0000-0000-0000-000000000000')
        self.assertEqual(response.status_code, 404)

    def test_list_project_documents(self):
        Document.objects.create(project=self.project, title='Doc 1')
        Document.objects.create(project=self.project, title='Doc 2')
        
        response = self.client.get(f'/api/projects/{self.project.id}/documents/list')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)


class SectionsAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(name='Test Project')
        self.document = Document.objects.create(
            project=self.project,
            title='Test Doc'
        )
        self.section = Section.objects.create(
            document=self.document,
            heading='Introduction',
            depth=1,
            order_index=0
        )
        SectionContent.objects.create(
            section=self.section,
            blocks_json={'version': 1, 'blocks': []}
        )

    def test_get_sections_tree(self):
        response = self.client.get(f'/api/documents/{self.document.id}/sections')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('tree', data)
        self.assertEqual(len(data['tree']), 1)
        self.assertEqual(data['tree'][0]['heading'], 'Introduction')

    def test_patch_section_rename(self):
        response = self.client.patch(
            f'/api/sections/{self.section.id}',
            data=json.dumps({'heading': 'New Title'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.section.refresh_from_db()
        self.assertEqual(self.section.heading, 'New Title')

    def test_patch_section_status(self):
        response = self.client.patch(
            f'/api/sections/{self.section.id}',
            data=json.dumps({'status': 'draft'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.section.refresh_from_db()
        self.assertEqual(self.section.status, 'draft')

    def test_verify_locks_section(self):
        response = self.client.patch(
            f'/api/sections/{self.section.id}',
            data=json.dumps({'status': 'verified'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.section.refresh_from_db()
        self.assertTrue(self.section.locked)
        self.assertEqual(self.section.status, 'verified')

    def test_locked_section_reopen(self):
        # First verify the section
        self.section.status = 'verified'
        self.section.locked = True
        self.section.save()
        
        # Try to reopen without reason
        response = self.client.patch(
            f'/api/sections/{self.section.id}',
            data=json.dumps({'status': 'draft'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # Reopen with reason
        response = self.client.patch(
            f'/api/sections/{self.section.id}',
            data=json.dumps({'status': 'draft', 'reopen_reason': 'Need updates'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.section.refresh_from_db()
        self.assertFalse(self.section.locked)
        self.assertEqual(self.section.reopen_reason, 'Need updates')

    def test_get_old_content(self):
        self.section.old_content_raw = 'Original text'
        self.section.save()
        
        response = self.client.get(f'/api/sections/{self.section.id}/old')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['old'], 'Original text')

    def test_get_new_content(self):
        response = self.client.get(f'/api/sections/{self.section.id}/new')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['version'], 1)
        self.assertEqual(data['blocks'], [])

    def test_put_new_content(self):
        blocks = {
            'version': 1,
            'blocks': [
                {'id': 'p1', 'type': 'paragraph', 'text': 'Hello world'}
            ]
        }
        response = self.client.put(
            f'/api/sections/{self.section.id}/new',
            data=json.dumps(blocks),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify content was saved
        self.section.refresh_from_db()
        content = self.section.content
        self.assertEqual(len(content.blocks_json['blocks']), 1)

    def test_put_invalid_blocks(self):
        blocks = {'version': 2, 'blocks': []}  # Invalid version
        response = self.client.put(
            f'/api/sections/{self.section.id}/new',
            data=json.dumps(blocks),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_locked_section_cannot_save_content(self):
        self.section.locked = True
        self.section.save()
        
        blocks = {'version': 1, 'blocks': []}
        response = self.client.put(
            f'/api/sections/{self.section.id}/new',
            data=json.dumps(blocks),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)


class MergeSectionsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(name='Test Project')
        self.document = Document.objects.create(
            project=self.project,
            title='Test Doc'
        )
        self.section1 = Section.objects.create(
            document=self.document,
            heading='Section 1',
            depth=1,
            order_index=0,
            old_content_raw='Content 1'
        )
        self.section2 = Section.objects.create(
            document=self.document,
            heading='Section 2',
            depth=1,
            order_index=1,
            old_content_raw='Content 2'
        )
        SectionContent.objects.create(section=self.section1, blocks_json={'version': 1, 'blocks': []})
        SectionContent.objects.create(section=self.section2, blocks_json={'version': 1, 'blocks': []})

    def test_merge_sections(self):
        response = self.client.post(
            '/api/sections/merge',
            data=json.dumps({
                'documentId': str(self.document.id),
                'sourceSectionIds': [str(self.section1.id), str(self.section2.id)],
                'targetHeading': 'Merged Section'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('newSectionId', data)
        
        # Verify old sections deleted
        self.assertEqual(
            Section.objects.filter(document=self.document).count(),
            1
        )
        
        # Verify merged content
        merged = Section.objects.get(id=data['newSectionId'])
        self.assertEqual(merged.heading, 'Merged Section')
        self.assertIn('Content 1', merged.old_content_raw)
        self.assertIn('Content 2', merged.old_content_raw)

    def test_merge_requires_two_sections(self):
        response = self.client.post(
            '/api/sections/merge',
            data=json.dumps({
                'documentId': str(self.document.id),
                'sourceSectionIds': [str(self.section1.id)],
                'targetHeading': 'Test'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)


class CommentsAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(name='Test Project')
        self.document = Document.objects.create(
            project=self.project,
            title='Test Doc'
        )
        self.section = Section.objects.create(
            document=self.document,
            heading='Test',
            depth=1
        )

    def test_list_comments_empty(self):
        response = self.client.get(f'/api/sections/{self.section.id}/comments')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_create_comment(self):
        response = self.client.post(
            f'/api/sections/{self.section.id}/comments',
            data=json.dumps({'body': 'This is a comment'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['body'], 'This is a comment')
        self.assertEqual(data['status'], 'open')

    def test_create_comment_requires_body(self):
        response = self.client.post(
            f'/api/sections/{self.section.id}/comments',
            data=json.dumps({'body': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)


class SnapshotsAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(name='Test Project')
        self.document = Document.objects.create(
            project=self.project,
            title='Test Doc'
        )
        self.section = Section.objects.create(
            document=self.document,
            heading='Test',
            depth=1
        )
        self.content = SectionContent.objects.create(
            section=self.section,
            blocks_json={'version': 1, 'blocks': [{'id': 'p1', 'type': 'paragraph', 'text': 'Test'}]}
        )

    def test_create_snapshot(self):
        response = self.client.post(
            f'/api/sections/{self.section.id}/snapshot',
            data=json.dumps({'reason': 'Before edit'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['reason'], 'Before edit')
        self.assertIn('blocks_json', data)

    def test_list_snapshots(self):
        Snapshot.objects.create(
            section=self.section,
            reason='Snapshot 1',
            blocks_json={'version': 1, 'blocks': []}
        )
        response = self.client.get(f'/api/sections/{self.section.id}/snapshots')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)

    def test_restore_snapshot(self):
        snapshot = Snapshot.objects.create(
            section=self.section,
            reason='Old version',
            blocks_json={'version': 1, 'blocks': [{'id': 'old', 'type': 'paragraph', 'text': 'Old content'}]}
        )
        
        response = self.client.post(
            f'/api/sections/{self.section.id}/snapshots/{snapshot.id}/restore'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify content was restored
        self.content.refresh_from_db()
        self.assertEqual(self.content.blocks_json['blocks'][0]['text'], 'Old content')


class TemplatesAPITest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_list_templates_empty(self):
        response = self.client.get('/api/templates')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_create_template(self):
        response = self.client.post(
            '/api/templates',
            data=json.dumps({
                'name': 'Custom Template',
                'mapping_json': {'styles': {'heading1': 'Title'}}
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['name'], 'Custom Template')

    def test_get_template_detail(self):
        template = Template.objects.create(
            name='Test Template',
            mapping_json={'styles': {}}
        )
        response = self.client.get(f'/api/templates/{template.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], 'Test Template')


class ExportPreflightTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(name='Test Project')
        self.document = Document.objects.create(
            project=self.project,
            title='Test Doc'
        )
        # Create sections with different statuses
        Section.objects.create(document=self.document, heading='S1', depth=1, status='verified')
        Section.objects.create(document=self.document, heading='S2', depth=1, status='draft')
        Section.objects.create(document=self.document, heading='S3', depth=1, status='not_started')

    def test_preflight_check(self):
        response = self.client.get(f'/api/documents/{self.document.id}/export/preflight')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['statusCounts']['total'], 3)
        self.assertEqual(data['statusCounts']['verified'], 1)
        self.assertEqual(data['statusCounts']['draft'], 1)
        self.assertEqual(data['statusCounts']['not_started'], 1)
        self.assertFalse(data['allVerified'])
        self.assertTrue(len(data['warnings']) > 0)


class AIEndpointTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(name='Test Project')
        self.document = Document.objects.create(
            project=self.project,
            title='Test Doc'
        )
        self.section = Section.objects.create(
            document=self.document,
            heading='Test',
            depth=1
        )

    def test_ai_section_endpoint(self):
        response = self.client.post(
            '/api/ai/section',
            data=json.dumps({
                'sectionId': str(self.section.id),
                'preset': 'modernize',
                'inputs': {'old': 'Some old text'},
                'options': {}
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['version'], 1)
        self.assertIn('blocks', data)

    def test_ai_requires_section_id(self):
        response = self.client.post(
            '/api/ai/section',
            data=json.dumps({
                'preset': 'modernize'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

