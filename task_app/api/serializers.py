from django.contrib.auth.models import User
from rest_framework import serializers

from task_app.models import Comment, Task
from user_auth_app.models import Profile


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model.
    
    Provides task data with calculated fields for comments count, 
    assignee details and reviewer details.
    """
    comments_count = serializers.SerializerMethodField()
    assignee = serializers.SerializerMethodField()
    reviewer = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ["id", "board", "title", "description", "status", "priority",
                  "assignee", "reviewer", "due_date", "comments_count"]

    def get_comments_count(self, obj):
        """
        Calculate the number of comments for a task.
        """
        return obj.comment.count()

    def get_assignee(self, obj):
        """
        Get detailed information about all assignees of a task.
        """
        assignee_list = obj.assignee.all()
        if not assignee_list.exists():
            return None
        result = []
        for assignee in assignee_list:
            if hasattr(assignee, "profile"):
                profile = assignee.profile
                result.append(
                    {"id": profile.id, "email": profile.user.email, "fullname": profile.fullname})
            else:
                result.append(
                    {"id": assignee.id, "email": assignee.user.email, "fullname": assignee.fullname})
        return result

    def get_reviewer(self, obj):
        """
        Get detailed information about all reviewers of a task.
        """
        reviewer_list = obj.reviewer.all()
        if not reviewer_list.exists():
            return None
        result = []
        for reviewer in reviewer_list:
            if hasattr(reviewer, "profile"):
                profile = reviewer.profile
                result.append(
                    {"id": profile.id, "email": profile.user.email, "fullname": profile.fullname})
            else:
                result.append(
                    {"id": reviewer.id, "email": reviewer.user.email, "fullname": reviewer.fullname})
        return result


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment model.
    
    Provides comment data with formatted created_at timestamp
    and author's full name.
    """
    created_at = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]

    def get_created_at(self, obj):
        """
        Format the timestamp of when the comment was created.
        """
        if obj.created_at:
            formatted_date = obj.created_at.strftime("%Y-%m-%dT%H:%M:%S")
            return formatted_date
        return None

    def get_author(self, obj):
        """
        Get the full name of the comment author.
        """
        if obj.author:
            author_name = Profile.objects.get(pk=obj.author.id).fullname
            return author_name
        return None
