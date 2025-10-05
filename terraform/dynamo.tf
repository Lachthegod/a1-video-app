
# // DynamoDB table
# resource "aws_dynamodb_table" "app_table" {
#   name         = "${var.project_prefix}-metadata"
#   billing_mode = "PAY_PER_REQUEST"
#   hash_key     = "user_id"
#   range_key    = "video_id"

#   attribute {
#     name = "user_id"
#     type = "S"
#   }

#   attribute {
#     name = "video_id"
#     type = "S"
#   }

#   tags = {
#     Project = "CAB432"
#   }
# }
