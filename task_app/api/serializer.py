from rest_framework import serializers

from task_app.models import Task


class TaskSerializer(serializers.ModelSerializer):
    comments_count = serializers.SerializerMethodField()
    assignee = serializers.SerializerMethodField()
    reviewer = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'priority',
                  'assignee', 'reviewer', 'due_date', 'comments_count']

    def get_comments_count(self, obj):
        return obj.comment.count()

    def get_assignee(self, obj):
        assignee_list = obj.assignee.all()
        if not assignee_list.exists():
            return None
        return [{"id": assignee.profile.id, "email": assignee.profile.email, "fullname": assignee.profile.fullname} for assignee in assignee_list]

    def get_reviewer(self, obj):
        reviewer_list = obj.reviewer.all()
        if not reviewer_list.exists():
            return None
        return [{"id": reviewer.profile.id, "email": reviewer.profile.email, "fullname": reviewer.profile.fullname} for reviewer in reviewer_list]
